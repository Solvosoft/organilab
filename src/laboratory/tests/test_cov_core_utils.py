from types import SimpleNamespace

from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from auth_and_perms.models import ProfilePermission, Rol
from laboratory import utils
from laboratory.models import (
    Laboratory,
    OrganizationStructure,
    OrganizationStructureRelations,
    Protocol,
    UserOrganization,
)


class BaseUtilsTest(TestCase):
    fixtures = ["laboratory_data.json"]

    def setUp(self):
        self.admin = User.objects.get(username="admin")
        self.sin_permisos = User.objects.get(username="tuwp")
        self.org = OrganizationStructure.objects.get(pk=1)
        self.lab = Laboratory.objects.get(pk=1)
        self.ct_lab = ContentType.objects.get_for_model(Laboratory)
        self.ct_org = ContentType.objects.get_for_model(OrganizationStructure)

    def dar_rol_administrativo_superior(self, profile):
        rol = Rol.objects.create(name="Administrativo superior")
        self.org.rol.add(rol)
        pp = ProfilePermission.objects.create(profile=profile, content_type=self.ct_org, object_id=self.org.pk)
        pp.rol.add(rol)
        return rol


class LaboratoriosDelUsuarioTest(BaseUtilsTest):

    def test_filtra_laboratorios_por_nombre(self):
        UserOrganization.objects.create(user=self.admin, organization=self.org, type_in_organization=1)
        labs = utils.get_user_laboratories(self.admin, q="ultra")
        self.assertEqual(list(labs), [Laboratory.objects.get(name="Lab Ultra")])

    def test_roles_de_la_organizacion_sin_instancia(self):
        roles = set(utils.get_rols_from_organization(self.org.pk))
        self.assertTrue(set(self.org.rol.values_list("pk", flat=True)) <= roles)

    def test_laboratorios_desde_organizacion(self):
        self.assertFalse(utils.get_laboratories_from_organization(99999, self.admin).exists())
        self.assertEqual(set(utils.get_laboratories_from_organization(self.org.pk, self.admin)), {1})
        self.dar_rol_administrativo_superior(self.admin.profile)
        self.assertEqual(set(utils.get_laboratories_from_organization(self.org.pk, self.admin)), {1, 2})

    def test_ids_de_laboratorio_con_rol_administrativo_superior(self):
        self.dar_rol_administrativo_superior(self.sin_permisos.profile)
        self.assertEqual(set(utils.get_lab_ids(self.org, self.sin_permisos.profile)), {1, 2})

    def test_objeto_relacionado_de_un_protocolo(self):
        protocolo = Protocol.objects.get(pk=1)
        self.assertEqual(utils.find_rel_object(protocolo), protocolo.laboratory)


class AncestrosYDescendientesTest(BaseUtilsTest):

    def setUp(self):
        super().setUp()
        self.hija = OrganizationStructure.objects.create(name="Hija", parent=self.org)
        self.nieta = OrganizationStructure.objects.create(name="Nieta", parent=self.hija)
        for org in (self.org, self.hija, self.nieta):
            UserOrganization.objects.create(user=self.admin, organization=org, type_in_organization=1)

    def test_organizaciones_ancestras_con_usuarios(self):
        """Con descendants=False se recorren los ancestros: antes fallaba por un typo
        (`acestors`) con AttributeError."""
        pks = set(utils.get_pk_org_ancestors(self.nieta.pk, descendants=False))
        self.assertEqual(pks, {self.org.pk, self.hija.pk, self.nieta.pk})
        self.assertEqual(set(utils.get_pk_org_ancestors(self.org.pk)), {self.org.pk, self.hija.pk, self.nieta.pk})

    def test_ancestros_y_descendientes_del_usuario(self):
        self.hija.users.add(self.admin)
        pks = utils.get_pk_org_ancestors_decendants(self.admin, self.hija.pk)
        self.assertEqual(set(pks), {self.org.pk, self.hija.pk, self.nieta.pk})


class AccesosTest(BaseUtilsTest):

    def test_perfil_y_accesos_sin_datos(self):
        self.assertTrue(utils.check_has_profile(self.admin))
        self.assertFalse(utils.check_user_access_kwargs_org_lab(1, 1, AnonymousUser()))
        self.assertFalse(utils.check_user_access_kwargs_org(self.org, self.admin))
        self.assertTrue(utils.check_user_access_kwargs_org(self.org.pk, self.admin))

    def vista(self, user, **kwargs):
        return SimpleNamespace(kwargs=kwargs, request=SimpleNamespace(user=user))

    def test_permiso_por_laboratorio_sin_parametros(self):
        permiso = utils.PermissionByLaboratoryInOrganization()
        self.assertFalse(permiso.has_permission(None, self.vista(self.admin, org_pk=1)))

    def test_permiso_por_organizacion(self):
        permiso = utils.PermissionByOrganization()
        self.assertFalse(permiso.has_permission(None, self.vista(self.admin)))
        vista = self.vista(self.admin, org_pk=self.org.pk)
        self.assertTrue(permiso.has_permission(None, vista))
        self.assertEqual(vista.organization, self.org)
        self.assertTrue(permiso.has_object_permission(None, vista, None))
        self.assertFalse(permiso.has_permission(None, self.vista(AnonymousUser(), org_pk=self.org.pk)))


class EliminarRelacionesDeLaboratorioTest(BaseUtilsTest):

    def setUp(self):
        super().setUp()
        self.rol_org = Rol.objects.create(name="Rol de la organización")
        self.rol_otro = Rol.objects.create(name="Rol ajeno")
        self.org.rol.add(self.rol_org)

    def crear_pp(self, *roles):
        pp = ProfilePermission.objects.create(
            profile=self.sin_permisos.profile, content_type=self.ct_lab, object_id=self.lab.pk, organization=self.org
        )
        pp.rol.add(*roles)
        return pp

    def test_lab_de_la_organizacion_borra_los_permisos(self):
        pp = self.crear_pp(self.rol_org)
        utils.delete_profile_roles_related_to_laboratory(ProfilePermission.objects.filter(pk=pp.pk), self.org, self.lab)
        self.assertFalse(ProfilePermission.objects.filter(pk=pp.pk).exists())

    def test_lab_ajeno_solo_quita_los_roles_de_la_organizacion(self):
        org_ajena = OrganizationStructure.objects.get(pk=3)
        org_ajena.rol.add(self.rol_org)
        solo_org = self.crear_pp(self.rol_org)
        mixto = self.crear_pp(self.rol_org, self.rol_otro)
        utils.delete_profile_roles_related_to_laboratory(
            ProfilePermission.objects.filter(pk__in=[solo_org.pk, mixto.pk]), org_ajena, self.lab
        )
        self.assertFalse(ProfilePermission.objects.filter(pk=solo_org.pk).exists())
        self.assertEqual(list(ProfilePermission.objects.get(pk=mixto.pk).rol.all()), [self.rol_otro])

    def test_borra_relaciones_y_deja_bitacora(self):
        relaciones = OrganizationStructureRelations.objects.filter(content_type=self.ct_lab, object_id=2)
        protocolos = Protocol.objects.filter(pk=1)
        lista = [
            {"list": relaciones, "model_name": "relación", "change_message": "%s / %s"},
            {"list": protocolos, "model_name": "protocolo", "change_message": "%s en %s (%s)"},
        ]
        utils.delete_relation_between_laboratory_with_other_models(lista, self.admin, self.lab)
        self.assertFalse(OrganizationStructureRelations.objects.filter(content_type=self.ct_lab, object_id=2).exists())
        self.assertFalse(Protocol.objects.filter(pk=1).exists())
        mensajes = list(LogEntry.objects.values_list("change_message", flat=True))
        self.assertIn("Vick Lab / Investigadores SA", mensajes)
        self.assertIn("Lavado de manos en Vick Lab (No organization)", mensajes)
