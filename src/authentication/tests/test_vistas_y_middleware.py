"""Vistas sueltas de `authentication` y las ramas de `ProfileMiddleware` que no pasan
por una URL normal."""

from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import Http404
from django.test import RequestFactory, override_settings
from django.urls import reverse

from auth_and_perms.models import AuthenticateDataRequest
from auth_and_perms.tests.escenario import EscenarioOrganizaciones
from authentication.middleware import ProfileMiddleware
from authentication.views import oidc_logout_url


class NotificacionFirmaDigitalTest(EscenarioOrganizaciones):
    url = "/perms/digitalsignature/notify"

    def setUp(self):
        self.usuario = self.crear_usuario("notificador", self.org_a)
        self.client.force_login(self.usuario)

    def test_notificacion_de_transaccion_existente_la_actualiza(self):
        solicitud = AuthenticateDataRequest.objects.create(identification="0101110111", id_transaction=77)
        response = self.client.post(
            self.url,
            data={"data": {"id_transaction": 77, "received_notification": True, "status": 0}},
            content_type="application/json",
        )
        self.assertEqual(response.json(), {"data": True})
        solicitud.refresh_from_db()
        self.assertTrue(solicitud.received_notification)
        self.assertEqual(solicitud.status, 0)

    def test_notificacion_de_transaccion_inexistente_no_crea_nada(self):
        response = self.client.post(
            self.url, data={"data": {"id_transaction": 404}}, content_type="application/json"
        )
        self.assertEqual(response.json(), {"data": None})
        self.assertFalse(AuthenticateDataRequest.objects.exists())

    def test_requiere_sesion(self):
        self.client.logout()
        response = self.client.post(
            self.url, data={"data": {"id_transaction": 1}}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)


class URLDeCierreOIDCTest(EscenarioOrganizaciones):
    def peticion(self, id_token=None):
        request = RequestFactory().get("/")
        SessionMiddleware(lambda r: None).process_request(request)
        if id_token:
            request.session["oidc_id_token"] = id_token
        return request

    def test_sin_id_token_vuelve_al_login(self):
        self.assertEqual(oidc_logout_url(self.peticion()), reverse("login"))

    @override_settings(OIDC_OP_LOGOUT_ENDPOINT="")
    def test_sin_endpoint_de_cierre_vuelve_al_login(self):
        self.assertEqual(oidc_logout_url(self.peticion("tok")), reverse("login"))

    @override_settings(OIDC_OP_LOGOUT_ENDPOINT="https://idp/logout", OIDC_POST_LOGOUT_REDIRECT_URL="")
    def test_cierre_en_el_proveedor_con_id_token(self):
        self.assertEqual(oidc_logout_url(self.peticion("tok")), "https://idp/logout?id_token_hint=tok")

    @override_settings(
        OIDC_OP_LOGOUT_ENDPOINT="https://idp/logout",
        OIDC_POST_LOGOUT_REDIRECT_URL="https://organilab/salida",
    )
    def test_cierre_con_redireccion_posterior(self):
        self.assertEqual(
            oidc_logout_url(self.peticion("tok")),
            "https://idp/logout?id_token_hint=tok&post_logout_redirect_uri=https%3A%2F%2Forganilab%2Fsalida",
        )


def vista_con_lab_pk(request, lab_pk=None):
    return None


vista_con_lab_pk.lab_pk_field = "lab_pk"


class ProfileMiddlewareTest(EscenarioOrganizaciones):
    def setUp(self):
        self.middleware = ProfileMiddleware(lambda request: None)

    def peticion(self, user):
        request = RequestFactory().get("/")
        request.user = user
        request.resolver_match = None
        return request

    def test_anonimo_no_se_toca(self):
        request = self.peticion(AnonymousUser())
        self.assertIsNone(self.middleware.process_view(request, vista_con_lab_pk, (), {}))

    def test_usuario_sin_perfil_da_404(self):
        user = User.objects.create_user("sin-perfil")
        with self.assertRaises(Http404):
            self.middleware.process_view(self.peticion(user), vista_con_lab_pk, (), {})

    def test_vista_funcion_con_lab_pk_field_suma_los_roles_del_laboratorio(self):
        user = self.crear_usuario("laboratorista", self.org_a)
        from auth_and_perms.models import ProfilePermission, Rol
        from auth_and_perms.tests.escenario import permisos

        rol = Rol.objects.create(name="Rol de laboratorio")
        rol.permissions.add(*permisos("laboratory.view_laboratory"))
        pp = ProfilePermission.objects.create(
            profile=user.profile, content_type=self.ct_lab, object_id=self.lab_a.pk, organization=self.org_a
        )
        pp.rol.add(rol)
        request = self.peticion(user)
        self.middleware.process_view(request, vista_con_lab_pk, (), {"lab_pk": self.lab_a.pk})
        self.assertIn("laboratory.view_laboratory", request.user._perm_cache)

        otro = self.peticion(User.objects.get(pk=user.pk))
        self.middleware.process_view(otro, vista_con_lab_pk, (), {"lab_pk": self.lab_b.pk})
        self.assertFalse(hasattr(otro.user, "_perm_cache"))

    def test_organizacion_inactiva_da_404(self):
        user = self.crear_usuario("miembro", self.org_b)
        self.org_b.active = False
        self.org_b.save()
        with self.assertRaises(Http404):
            self.middleware.process_view(self.peticion(user), vista_con_lab_pk, (), {"org_pk": self.org_b.pk})
