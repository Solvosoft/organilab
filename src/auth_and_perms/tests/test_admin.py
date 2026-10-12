"""El admin de Django para `auth_and_perms`: filtros, acciones y el borrado de usuarios
que conserva la bitácora."""

import io
import json
import zipfile

from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import override_settings
from django.urls import reverse

from auth_and_perms.models import AuthorizedApplication, Profile, ProfilePermission
from auth_and_perms.tests.escenario import EscenarioOrganizaciones


@override_settings(DELETED_USER_SENTINEL_USERNAME="centinela")
class AdminAuthAndPermsTest(EscenarioOrganizaciones):
    def setUp(self):
        self.admin = User.objects.create_superuser("superadmin", "superadmin@ejemplo.cr", "clave")
        Profile.objects.create(user=self.admin)
        self.centinela = User.objects.create_user("centinela")
        self.client.force_login(self.admin)

    def registrar(self, user, repr_):
        return LogEntry.objects.log_action(
            user.pk, ContentType.objects.get_for_model(User).pk, user.pk, repr_, ADDITION
        )

    def test_filtro_de_bitacora_reasignada_al_borrar_usuarios(self):
        self.registrar(self.admin, "Algo (Usuario eliminado: Ana (ana))")
        self.registrar(self.admin, "Algo (Deleted user: Bea (bea))")
        self.registrar(self.admin, "Entrada normal")
        url = reverse("admin:admin_logentry_changelist")
        response = self.client.get(url, {"reassigned_on_user_delete": "yes"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["cl"].result_count, 2)
        response = self.client.get(url)
        self.assertEqual(response.context["cl"].result_count, 3)

    def test_exportar_permisos_de_roles_en_zip(self):
        user = self.crear_usuario("exportado", self.org_a, perms=["laboratory.view_laboratory"])
        pp = ProfilePermission.objects.get(profile=user.profile)
        rol = pp.rol.get()
        response = self.client.post(
            reverse("admin:auth_and_perms_rol_changelist"),
            {"action": "export_rol_perms", "_selected_action": [rol.pk]},
        )
        self.assertEqual(response["Content-Type"], "application/x-zip-compressed")
        archivo = zipfile.ZipFile(io.BytesIO(response.content))
        self.assertEqual(archivo.namelist(), [f"{rol.name}.json"])
        filas = json.loads(archivo.read(f"{rol.name}.json"))
        self.assertEqual([fila["pk"] for fila in filas], [pp.pk])

    def test_listados_muestran_token_y_roles(self):
        AuthorizedApplication.objects.create(name="con-usuario", notification_url="https://a/", token="t")
        sin_usuario = AuthorizedApplication.objects.create(name="sin-usuario", notification_url="https://b/", token="t")
        AuthorizedApplication.objects.filter(pk=sin_usuario.pk).update(user=None)
        response = self.client.get(reverse("admin:auth_and_perms_authorizedapplication_changelist"))
        self.assertContains(response, "unknown")
        token = AuthorizedApplication.objects.get(name="con-usuario").user.auth_token.key
        self.assertContains(response, token)

        self.crear_usuario("con-roles", self.org_a, perms=["laboratory.view_laboratory"])
        response = self.client.get(reverse("admin:auth_and_perms_profilepermission_changelist"))
        self.assertContains(response, "Rol de con-roles")

    def test_borrar_un_usuario_reasigna_su_bitacora_al_centinela(self):
        user = User.objects.create_user("borrado", first_name="Bo", last_name="Rrado")
        entrada = self.registrar(user, "Creó algo")
        response = self.client.post(reverse("admin:auth_user_delete", args=[user.pk]), {"post": "yes"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=user.pk).exists())
        entrada.refresh_from_db()
        self.assertEqual(entrada.user, self.centinela)
        self.assertIn("Bo Rrado (borrado)", entrada.object_repr)

    def test_borrado_masivo_tambien_conserva_la_bitacora(self):
        uno = User.objects.create_user("uno")
        dos = User.objects.create_user("dos")
        e1, e2 = self.registrar(uno, "de uno"), self.registrar(dos, "de dos")
        response = self.client.post(
            reverse("admin:auth_user_changelist"),
            {"action": "delete_selected", "_selected_action": [uno.pk, dos.pk], "post": "yes"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk__in=[uno.pk, dos.pk]).exists())
        for entrada in (e1, e2):
            entrada.refresh_from_db()
            self.assertEqual(entrada.user, self.centinela)
