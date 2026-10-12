"""Funciones de apoyo de `auth_and_perms`: utilidades, árbol de organizaciones,
comprobaciones de acceso, etiquetas de plantilla y representaciones de modelos."""

from types import SimpleNamespace

from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.auth.models import AnonymousUser, Group, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.test import RequestFactory, override_settings
from rest_framework.authtoken.models import Token

from auth_and_perms.api.filterset import OrganizationStructureRelationsFilter
from auth_and_perms.djgentelellaimportorwidget import ImpostorWidget
from auth_and_perms.models import (
    AuthorizedApplication,
    GroupDescription,
    ImpostorLog,
    Profile,
    ProfilePermission,
    Rol,
)
from auth_and_perms.node_tree import get_tree_organization_pks_by_user
from auth_and_perms.organization_utils import (
    organization_can_change_laboratory,
    organization_permissions,
    user_is_allowed_on_organization,
)
from auth_and_perms.templatetags.user_rol_tags import has_perm_in_org
from auth_and_perms.tests.escenario import EscenarioOrganizaciones
from auth_and_perms.utils import (
    get_ip_address,
    get_roles_by_user,
    preserve_audit_trail_before_delete,
)
from laboratory.models import OrganizationStructure, OrganizationStructureRelations, UserOrganization


class AccesoAOrganizacionTest(EscenarioOrganizaciones):
    def test_sin_organizacion_no_hay_acceso(self):
        user = self.crear_usuario("alguien", self.org_a)
        with self.assertRaises(ObjectDoesNotExist):
            user_is_allowed_on_organization(user, None)

    def test_relacion_de_usuario_con_la_organizacion_da_acceso(self):
        user = self.crear_usuario("externo", self.org_b)
        user_org = UserOrganization.objects.get(user=user)
        OrganizationStructureRelations.objects.create(
            organization=self.org_a,
            content_type=ContentType.objects.get_for_model(UserOrganization),
            object_id=user_org.pk,
        )
        self.assertTrue(user_is_allowed_on_organization(user, self.org_a))

    def test_miembro_del_ancestro_tiene_acceso_a_la_hija(self):
        user = self.crear_usuario("de-la-raiz", self.org_a)
        self.assertTrue(user_is_allowed_on_organization(user, self.org_a_hija))

    def test_relacion_con_el_ancestro_da_acceso_a_la_hija(self):
        user = self.crear_usuario("relacionado", self.org_b)
        user_org = UserOrganization.objects.get(user=user)
        OrganizationStructureRelations.objects.create(
            organization=self.org_a,
            content_type=ContentType.objects.get_for_model(UserOrganization),
            object_id=user_org.pk,
        )
        self.assertTrue(user_is_allowed_on_organization(user, self.org_a_hija.pk))

    def test_organizacion_ajena_se_niega(self):
        user = self.crear_usuario("ajeno", self.org_b)
        with self.assertRaises(PermissionDenied):
            user_is_allowed_on_organization(user, self.org_a_hija)

    def test_laboratorio_relacionado_con_una_descendiente(self):
        OrganizationStructureRelations.objects.create(
            organization=self.org_a_hija, content_type=self.ct_lab, object_id=self.lab_b.pk
        )
        self.assertTrue(organization_can_change_laboratory(self.lab_b, self.org_a))
        self.assertFalse(organization_can_change_laboratory(self.lab_b, OrganizationStructure.objects.create(name="Otra")))

    def test_permisos_de_organizacion_de_un_inactivo_son_vacios(self):
        user = self.crear_usuario("inactivo", self.org_a, perms=["laboratory.view_laboratory"], is_active=False)
        self.assertEqual(organization_permissions(user, self.org_a), frozenset())
        self.assertEqual(organization_permissions(AnonymousUser(), self.org_a), frozenset())


class UtilidadesTest(EscenarioOrganizaciones):
    def test_roles_por_usuario_son_los_de_sus_organizaciones(self):
        user = self.crear_usuario("con-rol", self.org_a, perms=["laboratory.view_laboratory"])
        rol_ajeno = Rol.objects.create(name="Ajeno")
        self.org_b.rol.add(rol_ajeno)
        roles = get_roles_by_user(user)
        self.assertIn(Rol.objects.get(name="Rol de con-rol"), roles)
        self.assertNotIn(rol_ajeno, roles)

    def test_ip_toma_la_primera_de_x_forwarded_for(self):
        request = RequestFactory().get("/", HTTP_X_FORWARDED_FOR="10.0.0.1, 10.0.0.2")
        self.assertEqual(get_ip_address(request), "10.0.0.1")
        request = RequestFactory().get("/", HTTP_X_REAL_IP="10.0.0.9")
        self.assertEqual(get_ip_address(request), "10.0.0.9")

    def test_ip_de_una_peticion_sin_meta_es_vacia(self):
        self.assertEqual(get_ip_address(SimpleNamespace(META=None)), "")

    @override_settings(DELETED_USER_SENTINEL_USERNAME=None)
    def test_sin_centinela_no_se_reasigna_la_bitacora(self):
        user = User.objects.create_user("se-va")
        entrada = LogEntry.objects.log_action(
            user.pk, ContentType.objects.get_for_model(User).pk, user.pk, "se-va", ADDITION
        )
        preserve_audit_trail_before_delete(user)
        entrada.refresh_from_db()
        self.assertEqual(entrada.user, user)
        self.assertEqual(entrada.object_repr, "se-va")


class ArbolDeOrganizacionesTest(EscenarioOrganizaciones):
    def test_recorre_las_descendientes_del_usuario(self):
        user = self.crear_usuario("arbol", self.org_a)
        UserOrganization.objects.create(user=user, organization=self.org_a_hija)
        nieta = OrganizationStructure.objects.create(name="Nieta", parent=self.org_a_hija, level=2)
        UserOrganization.objects.create(user=user, organization=nieta)
        pks = []
        get_tree_organization_pks_by_user(self.org_a, user, pks, parents=set())
        self.assertEqual(pks, [self.org_a.pk, self.org_a_hija.pk, nieta.pk])

    def test_con_hijas_independientes_no_se_baja_mas(self):
        user = self.crear_usuario("arbol", self.org_a)
        UserOrganization.objects.create(user=user, organization=self.org_a_hija)
        self.org_a.enable_child_organizations = True
        self.org_a.save()
        pks = []
        get_tree_organization_pks_by_user(self.org_a, user, pks, parents=set())
        self.assertEqual(pks, [self.org_a.pk])
        pks = []
        get_tree_organization_pks_by_user(self.org_a_hija, user, pks, parents=set())
        self.assertEqual(pks, [])


class EtiquetasDeRolTest(EscenarioOrganizaciones):
    def contexto(self, user):
        request = RequestFactory().get("/")
        request.user = user
        return {"request": request}

    def test_superusuario_tiene_cualquier_permiso(self):
        su = User.objects.create_superuser("root", "root@ejemplo.cr", "clave")
        self.assertTrue(has_perm_in_org(self.contexto(su), self.org_b.pk, "laboratory.view_laboratory"))

    def test_organizacion_inexistente_no_da_permiso(self):
        user = self.crear_usuario("normal", self.org_a, perms=["laboratory.view_laboratory"])
        self.assertFalse(has_perm_in_org(self.contexto(user), 999999, "laboratory.view_laboratory"))


class RepresentacionDeModelosTest(EscenarioOrganizaciones):
    def test_perfil_sin_nombre_usa_el_username(self):
        user = self.crear_usuario("sin-nombre")
        self.assertEqual(str(user.profile), "sin-nombre")

    def test_profilepermission_describe_objetivo_y_roles(self):
        user = self.crear_usuario("descrito", self.org_a, perms=["laboratory.view_laboratory"])
        pp = ProfilePermission.objects.get(profile=user.profile)
        self.assertEqual(str(pp), "descrito · Organización A · Rol de descrito")
        huerfano = ProfilePermission.objects.create(
            profile=user.profile, content_type=self.ct_lab, object_id=999999
        )
        self.assertIn("#999999", str(huerfano))
        self.assertTrue(str(huerfano).endswith("no role"))
        self.assertTrue(str(ProfilePermission(profile=user.profile)).startswith("descrito · no target"))

    def test_impostorlog_genera_token_y_se_describe(self):
        a = self.crear_usuario("impostor")
        b = self.crear_usuario("suplantado")
        log = ImpostorLog.objects.create(impostor=a, imposted_as=b)
        self.assertEqual(len(log.token), 36)
        self.assertEqual(str(log), "impostor as suplantado")

    def test_descripcion_de_grupo_muestra_el_grupo(self):
        grupo = Group.objects.create(name="Grupo descrito")
        self.assertEqual(str(GroupDescription.objects.create(group=grupo)), "Grupo descrito")

    def test_aplicacion_autorizada_recibe_usuario_y_token(self):
        app = AuthorizedApplication.objects.create(name="firmador", notification_url="https://firmador/", token="x")
        app.refresh_from_db()
        self.assertEqual(app.user.username, "application/firmador")
        self.assertTrue(Token.objects.filter(user=app.user).exists())
        app.save()
        self.assertEqual(User.objects.filter(username__startswith="application/").count(), 1)


class WidgetImpostorTest(EscenarioOrganizaciones):
    def contexto(self, con_impostor):
        request = RequestFactory().get("/")
        if con_impostor:
            request.impostor_info = object()
        return {"context": {"request": request}, "item": SimpleNamespace(id=7, icon="fa fa-user")}

    def test_sin_suplantacion_no_hay_boton(self):
        widget = ImpostorWidget(self.contexto(False))
        self.assertEqual((widget.render(), widget.render_js(), widget.render_external_html()), ("", "", ""))
        self.assertEqual(widget.get_menu_item(), "")

    def test_con_suplantacion_el_boton_termina_la_sesion(self):
        html = ImpostorWidget(self.contexto(True)).get_menu_item()
        self.assertIn('id="fsb_7"', html)
        self.assertIn("/perms/end_switch_user", html)


class FiltroDeRelacionesTest(EscenarioOrganizaciones):
    def test_filtro_por_nombre_de_laboratorio(self):
        rel_a = OrganizationStructureRelations.objects.create(
            organization=self.org_a, content_type=self.ct_lab, object_id=self.lab_a.pk
        )
        OrganizationStructureRelations.objects.create(
            organization=self.org_a, content_type=self.ct_lab, object_id=self.lab_b.pk
        )
        qs = OrganizationStructureRelations.objects.all()
        filtro = OrganizationStructureRelationsFilter(data={"laboratory_name": "Laboratorio A"}, queryset=qs)
        self.assertEqual(list(filtro.qs), [rel_a])
        self.assertEqual(filtro.filter_laboratory_name(qs, "laboratory_name", ""), qs)
