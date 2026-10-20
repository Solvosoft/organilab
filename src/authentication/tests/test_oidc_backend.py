"""`OrganiLabOIDCBackend` con el proveedor simulado: ninguna prueba sale a la red.

Se ejercita el flujo de `mozilla_django_oidc` (`get_or_create_user`) parcheando la
única llamada HTTP que hace, la del endpoint `userinfo`.
"""

from unittest import mock

from django.contrib.auth.models import Group, User
from django.core.exceptions import SuspiciousOperation
from django.db import IntegrityError
from django.test import TestCase, override_settings

from auth_and_perms.models import Profile, ProfilePermission
from authentication.oidc_backend import OrganiLabOIDCBackend
from laboratory.models import OrganizationStructure, UserOrganization
from auth_and_perms.roles import ROLES
from auth_and_perms.tests.roles import require_role


def respuesta_userinfo(claims):
    respuesta = mock.Mock()
    respuesta.json.return_value = claims
    respuesta.raise_for_status.return_value = None
    return respuesta


class OIDCBackendTest(TestCase):
    def setUp(self):
        self.backend = OrganiLabOIDCBackend()

    def login(self, userinfo, id_token_payload=None):
        with mock.patch(
            "mozilla_django_oidc.auth.requests.get", return_value=respuesta_userinfo(userinfo)
        ) as get:
            user = self.backend.get_or_create_user("token", "id-token", id_token_payload or {})
        get.assert_called_once()
        return user

    def test_primer_ingreso_crea_usuario_y_perfil_con_los_claims(self):
        org = OrganizationStructure.objects.create(name="Universidad")
        rol = require_role(self, "estudiante")
        Group.objects.get_or_create(name="Profile")
        Group.objects.get_or_create(name="SGAView")
        with override_settings(DEFAULT_ORG_PK=org.pk, DEFAULT_ROL_NAME="estudiante"):
            user = self.login(
                {
                    "email": "ana@ejemplo.cr",
                    "given_name": "Ana",
                    "family_name": "Mora",
                    "phone_number": "8888-0000",
                    "address": {"formatted": "Heredia"},
                },
                id_token_payload={"sub": "abc-123"},
            )
        self.assertEqual(user.username, "ana@ejemplo.cr")
        self.assertEqual(user.get_full_name(), "Ana Mora")
        self.assertEqual(user.profile.phone_number, "8888-0000")
        self.assertEqual(user.profile.address, "Heredia")
        self.assertTrue(
            UserOrganization.objects.filter(
                user=user, organization=org, type_in_organization=UserOrganization.LABORATORY_USER
            ).exists()
        )
        pp = ProfilePermission.objects.get(profile=user.profile, object_id=org.pk)
        self.assertEqual(list(pp.rol.all()), [rol])
        esperados = set(
            Group.objects.filter(name__in=["Profile", "PendingTasks", "SGAView"]).values_list("name", flat=True)
        )
        self.assertTrue({"Profile", "SGAView"} <= esperados)
        self.assertEqual(set(user.groups.values_list("name", flat=True)), esperados)

    def test_rol_por_defecto_ya_asignado_no_se_duplica(self):
        org = OrganizationStructure.objects.create(name="Universidad")
        rol = require_role(self, "estudiante")
        user = User.objects.create_user("previo")
        profile = Profile.objects.create(user=user)
        with override_settings(DEFAULT_ORG_PK=org.pk, DEFAULT_ROL_NAME=ROLES["estudiante"]):
            self.backend._assign_default_org(profile)
            self.backend._assign_default_org(profile)
        pp = ProfilePermission.objects.get(profile=profile, object_id=org.pk)
        self.assertEqual(list(pp.rol.all()), [rol])

    def test_sin_organizacion_ni_rol_por_defecto_solo_crea_el_usuario(self):
        with override_settings(DEFAULT_ORG_PK=0, DEFAULT_ROL_NAME=""):
            user = self.login({"email": "solo@ejemplo.cr", "address": "Cartago"})
        self.assertEqual(user.profile.address, "Cartago")
        self.assertFalse(UserOrganization.objects.filter(user=user).exists())
        self.assertFalse(ProfilePermission.objects.filter(profile=user.profile).exists())

    def test_reingreso_actualiza_nombre_y_conserva_lo_que_no_viene(self):
        user = User.objects.create_user("ana", email="Ana@Ejemplo.cr", first_name="Ana", last_name="Vieja")
        user_logueado = self.login({"email": "ana@ejemplo.cr", "family_name": "Nueva"})
        self.assertEqual(user_logueado, user)
        user.refresh_from_db()
        self.assertEqual((user.first_name, user.last_name), ("Ana", "Nueva"))
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_los_claims_del_id_token_se_combinan_y_userinfo_manda(self):
        with mock.patch(
            "mozilla_django_oidc.auth.requests.get",
            return_value=respuesta_userinfo({"email": "nuevo@ejemplo.cr"}),
        ):
            claims = self.backend.get_userinfo(
                "token", "id-token", {"email": "viejo@ejemplo.cr", "given_name": "Luis"}
            )
        self.assertEqual(claims, {"email": "nuevo@ejemplo.cr", "given_name": "Luis"})

    def test_claims_sin_correo_ni_sub_se_rechazan(self):
        with self.assertRaises(SuspiciousOperation):
            self.login({"name": "Sin identidad"})

    def test_username_se_toma_de_username_luego_correo_luego_sub(self):
        self.assertEqual(self.backend._get_username({"username": "u", "email": "e@x.cr", "sub": "s"}), "u")
        self.assertEqual(self.backend._get_username({"email": "e@x.cr", "sub": "s"}), "e@x.cr")
        self.assertEqual(self.backend._get_username({"sub": "s" * 200}), "s" * 150)

    def test_sin_correo_no_se_busca_usuario_existente(self):
        self.assertFalse(self.backend.filter_users_by_claims({"sub": "abc"}).exists())

    def test_sin_correo_no_se_entra_con_otra_cuenta_de_correo_vacio(self):
        """Un login solo con `sub` creaba la cuenta... o devolvía la primera con correo vacío."""
        admin = User.objects.create_user("admin", email="")
        user = self.login({"sub": "externo-42"})
        self.assertNotEqual(user, admin)
        self.assertEqual(user.username, "externo-42")

    def test_conflicto_de_username_sin_correo_no_entrega_otra_cuenta(self):
        """El `sub` coincide con un username existente y no hay correo con el que desempatar."""
        User.objects.create_user("admin", email="")
        with self.assertRaises(IntegrityError):
            self.login({"sub": "admin"})

    def test_conflicto_de_username_falla_si_el_correo_no_existe(self):
        User.objects.create_user("ana", email="otra@ejemplo.cr")
        with self.assertRaises(IntegrityError):
            self.login({"username": "ana", "email": "ana@ejemplo.cr"})

    def test_conflicto_de_username_devuelve_quien_tiene_el_correo(self):
        """Carrera: el usuario con ese correo aparece entre la búsqueda y la creación."""
        existente = User.objects.create_user("ana", email="ana@ejemplo.cr")
        vacio = User.objects.none()
        encontrado = User.objects.filter(pk=existente.pk)
        with mock.patch.object(User.objects, "filter", side_effect=[vacio, encontrado]):
            with mock.patch.object(User.objects, "create_user", side_effect=IntegrityError):
                user = self.backend.create_user({"username": "ana", "email": "ana@ejemplo.cr"})
        self.assertEqual(user, existente)

    def test_correo_repetido_devuelve_el_primero(self):
        primero = User.objects.create_user("uno", email="dup@ejemplo.cr")
        User.objects.create_user("dos", email="DUP@ejemplo.cr")
        user = self.backend.create_user({"email": "dup@ejemplo.cr"})
        self.assertEqual(user, primero)
