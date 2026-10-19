"""Ramas de `auth_and_perms` que las pruebas por funcionalidad no alcanzaban.

Cada prueba fija un comportamiento observable (respuesta, error de validación, filas
creadas); no se limita a ejecutar líneas.
"""

from unittest import mock

from django.contrib.auth.models import Group, User
from django.urls import reverse

from auth_and_perms.api.serializers import ValidateUserAccessOrgLabSerializer
from auth_and_perms.forms import ProfileGroupForm
from auth_and_perms.models import Profile, ProfilePermission, Rol
from auth_and_perms.organization_utils import user_is_allowed_on_organization
from auth_and_perms.tests.escenario import EscenarioOrganizaciones
from auth_and_perms.views.user_org_creation import create_user_organization
from laboratory.models import (
    Catalog,
    Furniture,
    LaboratoryRoom,
    Object,
    OrganizationStructure,
    OrganizationStructureRelations,
    Shelf,
    ShelfObject,
    UserOrganization,
)
from auth_and_perms.roles import ROLES

XHR = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


class AccesoOrgLabViaHijaTest(EscenarioOrganizaciones):
    """`ValidateUserAccessOrgLabSerializer` con un laboratorio que la organización solo
    alcanza a través de una hija: el caso que obliga a mirar los descendientes."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # El laboratorio de la hija se relaciona con la hija, no con la raíz: la raíz no
        # es dueña ni tiene relación directa.
        OrganizationStructureRelations.objects.create(
            organization=cls.org_a_hija, content_type=cls.ct_lab, object_id=cls.lab_a_hija.pk
        )
        unidad = Catalog.objects.create(key="units", description="Litros")
        tipo_estante = Catalog.objects.create(key="container_type", description="Estante")
        tipo_mueble = Catalog.objects.create(key="furniture_type", description="Gabinete")
        sala = LaboratoryRoom.objects.create(laboratory=cls.lab_a_hija, name="Sala 1")
        mueble = Furniture.objects.create(labroom=sala, name="Mueble", type=tipo_mueble, dataconfig="[[[]]]")
        cls.estante = Shelf.objects.create(
            furniture=mueble, name="Estante", type=tipo_estante, quantity=10, measurement_unit=unidad
        )
        objeto = Object.objects.create(
            code="R-1", name="Acetona", organization=cls.org_a_hija, type=Object.REACTIVE
        )
        cls.envase = ShelfObject.objects.create(
            object=objeto, shelf=cls.estante, quantity=1, limit_quantity=0,
            measurement_unit=unidad, in_where_laboratory=cls.lab_a_hija,
        )

    def setUp(self):
        self.usuario = self.crear_usuario("acceso-a", self.org_a, perms=["laboratory.view_laboratory"])

    def validar(self, **extra):
        data = {"laboratory": self.lab_a_hija.pk, "organization": self.org_a.pk, **extra}
        return ValidateUserAccessOrgLabSerializer(data=data, context={"user": self.usuario})

    def test_objeto_y_estante_de_un_laboratorio_de_la_hija_son_validos(self):
        serializer = self.validar(shelfobject=self.envase.pk, shelf=self.estante.pk)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["shelfobject"], self.envase)

    def test_solo_el_estante(self):
        serializer = self.validar(shelf=self.estante.pk)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_sin_relacion_ni_con_la_hija_se_rechaza_antes(self):
        """El rechazo por organización lo da `super().validate()`: por eso la rama
        propia del serializer quedó marcada como defensa inalcanzable."""
        OrganizationStructureRelations.objects.filter(object_id=self.lab_a_hija.pk).delete()
        serializer = self.validar(shelfobject=self.envase.pk)
        self.assertFalse(serializer.is_valid())
        self.assertIn("organization", serializer.errors)


class FormularioGruposPorPerfilTest(EscenarioOrganizaciones):
    def test_sin_organizacion_solo_reporta_el_campo_obligatorio(self):
        user = self.crear_usuario("con-grupos", self.org_a)
        grupo = Group.objects.create(name="Grupo X")
        form = ProfileGroupForm(data={"profile": user.pk, "groups": [grupo.pk]})
        self.assertFalse(form.is_valid())
        # Solo el «obligatorio» del campo: `clean` no intenta buscar una organización
        # que no llegó.
        self.assertEqual(len(form.errors["organization"]), 1)


class Select2Cov2Base(EscenarioOrganizaciones):
    def setUp(self):
        self.admin_a = self.crear_usuario(
            "admin-a", self.org_a, perms=["laboratory.view_laboratory"], ambito="perfil"
        )
        self.client.force_login(self.admin_a)


class Select2FormularioInvalidoTest(Select2Cov2Base):
    """`RelOrganizationPKIntForm` es inválido con una organización existente pero un
    `laboratory` que no es número: cada select2 responde a su manera."""

    def get(self, name):
        return self.client.get(reverse(name), {"organization": self.org_a.pk, "laboratory": "x"}, **XHR)

    def test_usuarios_de_laboratorio_responden_400_con_los_errores(self):
        response = self.get("laborguserbase-list")
        self.assertEqual(response.status_code, 400)
        self.assertIn("laboratory", response.json()["errors"])

    def test_laboratorios_relacionables_dan_404(self):
        self.assertEqual(self.get("relorgbase-list").status_code, 404)

    def test_laboratorios_relacionables_completos_dan_404(self):
        self.assertEqual(self.get("relorgfullbase-list").status_code, 404)


class Select2GruposYUsuariosTest(Select2Cov2Base):
    def test_grupos_del_perfil(self):
        grupo = Group.objects.create(name="Grupo del perfil")
        self.admin_a.groups.add(grupo)
        response = self.client.get(reverse("groupsbyprofile-list"), {"profile": self.admin_a.pk})
        self.assertEqual([r["text"] for r in response.json()["results"]], ["Grupo del perfil"])

    def test_usuarios_sin_organizacion_dan_400(self):
        # Una organización inactiva o no numérica la corta antes `ProfileMiddleware`
        # (404); sin organización llega al serializer.
        response = self.client.get(reverse("usersbyorg-list"), **XHR)
        self.assertEqual(response.status_code, 400)
        self.assertIn("organization", response.json()["errors"])


class QuitarUsuarioSoloPorDeleteTest(EscenarioOrganizaciones):
    def test_get_no_borra_nada(self):
        """El `list` que reenviaba a `delete` se quitó: `http_method_names` solo admite
        DELETE, así que un GET nunca llegaba a él."""
        admin = self.crear_usuario("admin-del", self.org_a, perms=["auth_and_perms.view_profile"], ambito="perfil")
        self.client.force_login(admin)
        response = self.client.get(reverse("auth_and_perms:api-deluserorgcontt-list"), **XHR)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(self.org_a.users.filter(pk=admin.pk).exists())


class RelacionesOrgLabTest(EscenarioOrganizaciones):
    def test_lista_solo_las_relaciones_con_laboratorios_de_la_organizacion(self):
        admin = self.crear_usuario(
            "admin-rel", self.org_a,
            perms=["laboratory.view_organizationstructurerelations"], ambito="perfil",
        )
        relacion = OrganizationStructureRelations.objects.create(
            organization=self.org_a, content_type=self.ct_lab, object_id=self.lab_a.pk
        )
        # Una relación con otro tipo de objeto no es un laboratorio vinculado.
        OrganizationStructureRelations.objects.create(
            organization=self.org_a, content_type=self.ct_org, object_id=self.org_b.pk
        )
        self.client.force_login(admin)
        url = reverse("auth_and_perms:api-org-lab-relation-list", kwargs={"org_pk": self.org_a.pk})
        response = self.client.get(url, **XHR)
        self.assertEqual(response.status_code, 200, response.content[:300])
        self.assertEqual([fila["id"] for fila in response.json()["data"]], [relacion.pk])


class LoginBCCRTest(EscenarioOrganizaciones):
    def test_sin_identificacion_da_404(self):
        """Antes devolvía la excepción `Http404()` en vez de lanzarla y Django respondía 500."""
        response = self.client.post(reverse("auth_and_perms:login_with_bccr"), data={}, **XHR)
        self.assertEqual(response.status_code, 404)

    @mock.patch("auth_and_perms.views.fva_rest_authentication.requests.post")
    @mock.patch("auth_and_perms.views.fva_rest_authentication.ClienteAutenticador")
    def test_si_falla_el_aviso_a_la_aplicacion_igual_responde(self, cliente, post):
        """Sin aplicación autorizada, avisarle falla; la solicitud sigue su curso."""
        cliente.return_value.validar_servicio.return_value = True
        cliente.return_value.solicitar_autenticacion.return_value = {
            "id_solicitud": 21,
            "codigo_verificacion": "ZX9",
            "codigo_error": 0,
            "texto_codigo_error": "",
            "tiempo_maximo": 5,
        }
        response = self.client.post(reverse("auth_and_perms:login_with_bccr"), data={"Identificacion": "0101110111"})
        datos = response.json()
        self.assertEqual(datos["CodigoDeVerificacion"], "ZX9")
        self.assertEqual(datos["ResumenDelDocumento"], "")
        post.assert_not_called()


class CacheDePertenenciaTest(EscenarioOrganizaciones):
    def test_usuario_que_no_admite_atributos_igual_se_autoriza(self):
        """Si el objeto usuario no deja guardar la caché, se sigue sin ella."""
        user = self.crear_usuario("sin-cache", self.org_a)

        def sin_atributos(obj, name, value):
            if name == "_org_allowed_cache":
                raise AttributeError(name)
            object.__setattr__(obj, name, value)

        with mock.patch.object(User, "__setattr__", sin_atributos):
            self.assertTrue(user_is_allowed_on_organization(user, self.org_a))
        self.assertFalse(hasattr(user, "_org_allowed_cache"))


class CrearUsuarioDeOrganizacionTest(EscenarioOrganizaciones):
    """`create_user_organization`, que usa el comando `create_demo_organizations`."""

    datos = {"phone_number": "8888-8888", "id_card": "1-1111-1111", "job_position": ROLES["regente"], "language": "es"}

    def test_con_nombre_crea_la_organizacion_y_lo_hace_administrador(self):
        Group.objects.get_or_create(name="Profile")
        user = User.objects.create_user("demo-1")
        create_user_organization(user, "Org demo", self.datos)
        org = OrganizationStructure.objects.get(name="Org demo")
        self.assertEqual(user.profile.id_card, "1-1111-1111")
        self.assertTrue(UserOrganization.objects.filter(user=user, organization=org).exists())
        self.assertTrue(
            Rol.objects.filter(name=ROLES["organization_management"], organizationstructure=org).exists()
        )
        self.assertTrue(user.groups.filter(name="Profile").exists())

    def test_con_organizacion_existente_la_reutiliza(self):
        user = User.objects.create_user("demo-2")
        antes = OrganizationStructure.objects.count()
        create_user_organization(user, self.org_b, self.datos, user_type=UserOrganization.LABORATORY_USER)
        self.assertEqual(OrganizationStructure.objects.count(), antes)
        self.assertTrue(
            UserOrganization.objects.filter(
                user=user, organization=self.org_b, type_in_organization=UserOrganization.LABORATORY_USER
            ).exists()
        )
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertTrue(ProfilePermission.objects.filter(profile=user.profile, object_id=self.org_b.pk).exists())
