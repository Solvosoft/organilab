"""Vistas de gestión de organizaciones (`views/organizationstructure.py`) y las rutas
sueltas de registro, firma digital y medios."""

from unittest import mock

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import RequestFactory
from django.urls import reverse
from django_otp.plugins.otp_totp.models import TOTPDevice

from auth_and_perms.api.serializers import (
    OrganizationStructureRelationsSerializer,
    ValidateOrganizationSerializer,
)
from auth_and_perms.models import AuthenticateDataRequest, AuthorizedApplication, ProfilePermission, Rol
from auth_and_perms.tests.escenario import EscenarioOrganizaciones
from auth_and_perms.views import media_access
from auth_and_perms.views.user_org_creation import set_rol_administrator_on_org
from laboratory.models import UserOrganization
from report.models import TaskReport
from auth_and_perms.roles import ROLE_DEFINITIONS, ROLES


class GestionDeOrganizacionBase(EscenarioOrganizaciones):
    def setUp(self):
        self.admin_a = self.crear_usuario(
            "admin-a",
            self.org_a,
            perms=[
                "laboratory.change_organizationstructure",
                "auth_and_perms.view_rol",
                "auth_and_perms.change_rol",
            ],
            ambito="perfil",
        )
        self.client.force_login(self.admin_a)

    def mensajes(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]


class UsuariosDeOrganizacionTest(GestionDeOrganizacionBase):
    def test_agregar_un_usuario_nuevo(self):
        nuevo = self.crear_usuario("nuevo")
        response = self.client.post(
            reverse("auth_and_perms:addusersorganization", args=[self.org_a.pk]),
            data={"users": [self.admin_a.pk, nuevo.pk]},
        )
        self.assertRedirects(response, reverse("auth_and_perms:organizationManager"), fetch_redirect_response=False)
        self.assertTrue(
            UserOrganization.objects.filter(
                user=nuevo, organization=self.org_a, type_in_organization=UserOrganization.LABORATORY_USER
            ).exists()
        )

    def test_quitar_a_quien_esta_en_varias_organizaciones_le_quita_los_roles_de_esta(self):
        varios = self.crear_usuario("varios", self.org_a, type_in_organization=UserOrganization.LABORATORY_USER)
        UserOrganization.objects.create(user=varios, organization=self.org_b)
        rol = Rol.objects.create(name="Rol de A con permisos")
        rol.permissions.add(*Rol.objects.get(name="Rol de admin-a").permissions.all())
        self.org_a.rol.add(rol)
        pp = ProfilePermission.objects.create(
            profile=varios.profile, content_type=self.ct_lab, object_id=self.lab_b.pk
        )
        pp.rol.add(rol)
        self.client.post(
            reverse("auth_and_perms:addusersorganization", args=[self.org_a.pk]),
            data={"users": [self.admin_a.pk]},
        )
        self.assertFalse(pp.rol.exists())
        self.assertFalse(self.org_a.users.filter(pk=varios.pk).exists())


class AdministradoresYRolesTest(GestionDeOrganizacionBase):
    def test_administradores_activos_de_la_organizacion(self):
        jefe = self.crear_usuario("jefe", self.org_a, first_name="Jefa", last_name="Mora")
        rol = Rol.objects.create(name=ROLES["administrativo_superior"])
        pp = ProfilePermission.objects.create(profile=jefe.profile, content_type=self.ct_org, object_id=self.org_a.pk)
        pp.rol.add(rol)
        response = self.client.get(reverse("auth_and_perms:get_org_administrators", args=[self.org_a.pk]))
        self.assertEqual(response.json(), {"users": [{"name": "Jefa Mora", "email": "jefe@ejemplo.cr"}]})

    def test_administradores_de_una_organizacion_ajena_se_niegan(self):
        response = self.client.get(reverse("auth_and_perms:get_org_administrators", args=[self.org_b.pk]))
        self.assertNegado(response, 403)

    def test_obtener_un_rol(self):
        rol = Rol.objects.create(name="Consulta", description="Solo ver")
        response = self.client.get(reverse("auth_and_perms:get_rol", args=[rol.pk]))
        self.assertEqual(response.json(), {"name": "Consulta", "description": "Solo ver"})

    def test_actualizar_un_rol_de_la_organizacion(self):
        rol = Rol.objects.create(name="Viejo")
        self.org_a.rol.add(rol)
        url = reverse("auth_and_perms:update_rol", args=[self.org_a.pk, rol.pk])
        lista = reverse("auth_and_perms:list_rol_by_org", kwargs={"org_pk": self.org_a.pk})
        response = self.client.post(url, data={"name": "Nuevo", "description": "d"})
        self.assertRedirects(response, lista, fetch_redirect_response=False)
        rol.refresh_from_db()
        self.assertEqual(rol.name, "Nuevo")
        response = self.client.post(url, data={"name": "x" * 200})
        self.assertRedirects(response, lista, fetch_redirect_response=False)
        self.assertEqual(self.mensajes(response)[-1], "Error, form is invalid")

    def test_no_se_actualiza_un_rol_de_otra_organizacion(self):
        ajeno = Rol.objects.create(name="Ajeno")
        self.org_b.rol.add(ajeno)
        response = self.client.post(
            reverse("auth_and_perms:update_rol", args=[self.org_a.pk, ajeno.pk]), data={"name": "Tomado"}
        )
        self.assertNegado(response, 404)
        ajeno.refresh_from_db()
        self.assertEqual(ajeno.name, "Ajeno")


class OrganizacionesHijasTest(GestionDeOrganizacionBase):
    def test_habilitar_y_deshabilitar(self):
        url = reverse("auth_and_perms:enable_child_organizations")
        self.client.post(url, data={"organization": self.org_a.pk, "enable": "true"})
        self.org_a.refresh_from_db()
        self.assertTrue(self.org_a.enable_child_organizations)
        response = self.client.post(url, data={"organization": self.org_a.pk, "enable": "false"})
        self.assertRedirects(response, reverse("auth_and_perms:organizationManager"), fetch_redirect_response=False)
        self.org_a.refresh_from_db()
        self.assertFalse(self.org_a.enable_child_organizations)

    def test_organizacion_ajena_se_niega(self):
        response = self.client.post(
            reverse("auth_and_perms:enable_child_organizations"),
            data={"organization": self.org_b.pk, "enable": "true"},
        )
        self.assertNegado(response, 403)
        self.org_b.refresh_from_db()
        self.assertFalse(self.org_b.enable_child_organizations)


class AdministradorDeOrganizacionHijaTest(EscenarioOrganizaciones):
    def test_en_una_hija_reutiliza_el_rol_de_gestion_de_la_raiz(self):
        raiz_admin = self.crear_usuario("raiz-admin")
        set_rol_administrator_on_org(raiz_admin.profile, self.org_a)
        rol = Rol.objects.get(name=ROLES["organization_management"], organizationstructure=self.org_a)
        self.assertEqual(rol.description, ROLE_DEFINITIONS["organization_management"]["description"])
        hija_admin = self.crear_usuario("hija-admin")
        set_rol_administrator_on_org(hija_admin.profile, self.org_a_hija)
        pp = ProfilePermission.objects.get(profile=hija_admin.profile, object_id=self.org_a_hija.pk)
        self.assertEqual(list(pp.rol.all()), [rol])


class RegistroYFirmaDigitalTest(EscenarioOrganizaciones):
    def test_qr_del_dispositivo_totp(self):
        user = self.crear_usuario("con-totp")
        TOTPDevice.objects.create(user=user, name="con-totp")
        response = self.client.get(reverse("auth_and_perms:show_qr_img", args=[user.pk]))
        self.assertEqual(response["Content-Type"], "image/svg+xml")
        self.assertIn(b"<svg", response.content)

    @mock.patch("auth_and_perms.views.fva_rest_authentication.requests.post")
    @mock.patch("auth_and_perms.views.fva_rest_authentication.ClienteAutenticador")
    def test_login_con_bccr_registra_la_solicitud(self, cliente, post):
        AuthorizedApplication.objects.create(name="firmador", notification_url="https://firmador/", token="t")
        cliente.return_value.validar_servicio.return_value = True
        cliente.return_value.solicitar_autenticacion.return_value = {
            "id_solicitud": 15,
            "codigo_verificacion": "AB12",
            "codigo_error": 0,
            "texto_codigo_error": "",
            "tiempo_maximo": 5,
            "resumen": "Resumen",
        }
        response = self.client.post(reverse("auth_and_perms:login_with_bccr"), data={"Identificacion": "0101110111"})
        datos = response.json()
        self.assertTrue(datos["FueExitosaLaSolicitud"])
        self.assertEqual(datos["CodigoDeVerificacion"], "AB12")
        self.assertEqual(datos["ResumenDelDocumento"], "Resumen")
        post.assert_called_once()
        solicitud = AuthenticateDataRequest.objects.get(id_transaction=15)
        self.assertEqual(self.client.session["authenticatedata"], solicitud.pk)

    @mock.patch("auth_and_perms.views.fva_rest_authentication.ClienteAutenticador")
    def test_login_con_bccr_sin_servicio(self, cliente):
        cliente.return_value.validar_servicio.return_value = False
        cliente.return_value.DEFAULT_ERROR = {
            "id_solicitud": 0,
            "codigo_verificacion": None,
            "codigo_error": 1,
            "texto_codigo_error": "No disponible",
            "tiempo_maximo": 1,
        }
        response = self.client.post(reverse("auth_and_perms:login_with_bccr"), data={"Identificacion": "0101110111"})
        datos = response.json()
        self.assertFalse(datos["FueExitosaLaSolicitud"])
        self.assertEqual(datos["DescripcionDelError"], "No disponible")
        self.assertEqual(AuthenticateDataRequest.objects.get().code, "N/D")

    def test_estado_de_firma(self):
        url = reverse("auth_and_perms:check_signature_window_status_register")
        response = self.client.get(url, {"callback": "cb", "IdDeLaSolicitud": 9})
        self.assertIn(b"Transacci", response.content)
        self.assertTrue(response.content.startswith(b"cb("))

        solicitud = AuthenticateDataRequest.objects.create(id_transaction=9, status=0, received_notification=True)
        session = self.client.session
        session["authenticatedata"] = solicitud.pk
        session.save()
        response = self.client.get(url, {"callback": "cb", "IdDeLaSolicitud": 9})
        self.assertIn(b'"SeRealizo": true', response.content)
        self.assertNotIn("authenticatedata", self.client.session)

    def test_estado_de_firma_rechaza_callback_que_no_es_identificador(self):
        response = self.client.get(
            reverse("auth_and_perms:check_signature_window_status_register"),
            {"callback": "<script>alert(1)</script>", "IdDeLaSolicitud": 9},
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn(b"<script>", response.content)


class AccesoAMediosTest(EscenarioOrganizaciones):
    def peticion(self, path, user):
        request = RequestFactory().get("/media/" + path)
        request.user = user
        return media_access(request, path)

    def test_reportes_solo_para_quien_los_creo(self):
        duena = self.crear_usuario("duena")
        otro = self.crear_usuario("otro")
        TaskReport.objects.create(created_by=duena, type_report="x", file_type="pdf", file="report/r1.pdf")
        response = self.peticion("report/r1.pdf", duena)
        self.assertEqual(response["X-Accel-Redirect"], "/protected/report/r1.pdf")
        self.assertEqual(self.peticion("report/r1.pdf", otro).status_code, 403)
        from django.contrib.auth.models import AnonymousUser

        self.assertEqual(self.peticion("report/r1.pdf", AnonymousUser()).status_code, 403)


class SerializadoresTest(EscenarioOrganizaciones):
    def test_organizacion_inactiva_no_valida(self):
        self.org_b.active = False
        self.org_b.save()
        serializer = ValidateOrganizationSerializer(data={"organization": self.org_b.pk})
        self.assertFalse(serializer.is_valid())
        self.assertIn("organization", serializer.errors)

    def test_nombre_de_laboratorio_desde_diccionario(self):
        serializer = OrganizationStructureRelationsSerializer()
        self.assertEqual(serializer.get_laboratory_name({"object_id": self.lab_a.pk}), "Laboratorio A")
        self.assertEqual(serializer.get_laboratory_name({"object_id": 999999}), "999999")
