"""Suplantación de usuarios (`views/impostor.py` + `ImpostorMiddleware`) y
`ProfileLanguageMiddleware`."""

from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory
from django.urls import reverse
from django.utils.timezone import now

from auth_and_perms.middleware import ImpostorMiddleware
from auth_and_perms.models import ImpostorLog, RegistrationUser
from auth_and_perms.tests.escenario import EscenarioOrganizaciones


class SuplantacionTest(EscenarioOrganizaciones):
    def setUp(self):
        self.soporte = self.crear_usuario(
            "soporte", self.org_a, perms=["auth_and_perms.change_impostorlog"]
        )
        self.miembro = self.crear_usuario("miembro", self.org_a)
        self.ajeno = self.crear_usuario("ajeno", self.org_b)
        self.client.force_login(self.soporte)

    def suplantar(self, user, org=None):
        org = org or self.org_a
        return self.client.get(
            reverse("auth_and_perms:change_to_impostor", args=[org.pk, user.pk])
        )

    def mensajes(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]

    def test_suplantar_a_un_miembro_cambia_el_usuario_de_las_peticiones(self):
        response = self.suplantar(self.miembro)
        self.assertRedirects(response, reverse("index"), fetch_redirect_response=False)
        log = ImpostorLog.objects.get(impostor=self.soporte, imposted_as=self.miembro, active=True)
        self.assertEqual(response.cookies["impostor_token"].value, log.token)
        self.assertEqual(self.client.session["impostor"], self.miembro.pk)

        response = self.client.get(reverse("auth_and_perms:select_organization_by_user"))
        self.assertEqual(response.wsgi_request.user.pk, self.miembro.pk)
        self.assertEqual(response.wsgi_request.impostor_info, log)

    def test_token_que_no_coincide_no_suplanta(self):
        self.suplantar(self.miembro)
        self.client.cookies["impostor_token"] = "otro-token"
        response = self.client.get(reverse("auth_and_perms:select_organization_by_user"))
        self.assertEqual(response.wsgi_request.user.pk, self.soporte.pk)

    def test_segunda_suplantacion_activa_avisa(self):
        ImpostorLog.objects.create(impostor=self.soporte, imposted_as=self.miembro, impostor_ip="127.0.0.1")
        response = self.suplantar(self.miembro)
        self.assertIn("You have active impostor session", self.mensajes(response)[-1])
        self.assertEqual(ImpostorLog.objects.filter(impostor=self.soporte).count(), 1)

    def test_no_se_puede_suplantar_a_si_mismo(self):
        response = self.suplantar(self.soporte)
        self.assertEqual(self.mensajes(response), ["Request User is the same as current user"])
        self.assertFalse(ImpostorLog.objects.exists())

    def test_usuario_fuera_de_la_organizacion(self):
        response = self.suplantar(self.ajeno)
        self.assertEqual(self.mensajes(response), ["User not in organization"])
        self.assertFalse(ImpostorLog.objects.exists())

    def test_organizacion_ajena_se_niega(self):
        response = self.suplantar(self.ajeno, org=self.org_b)
        self.assertNegado(response, 403)
        self.assertFalse(ImpostorLog.objects.exists())

    def test_sin_permiso_se_niega(self):
        self.client.force_login(self.miembro)
        response = self.suplantar(self.soporte)
        self.assertNegado(response, 403)

    def test_terminar_todas_desde_la_sesion_suplantada(self):
        self.suplantar(self.miembro)
        response = self.client.get(reverse("auth_and_perms:remove_impostor"), {"all": 1})
        self.assertRedirects(response, reverse("index"), fetch_redirect_response=False)
        log = ImpostorLog.objects.get()
        self.assertFalse(log.active)
        self.assertIsNotNone(log.logged_out)
        self.assertNotIn("impostor", self.client.session)
        self.assertEqual(response.cookies["impostor_token"].value, "")

    def test_terminar_todas_sin_estar_suplantando(self):
        ImpostorLog.objects.create(impostor=self.soporte, imposted_as=self.miembro, impostor_ip="127.0.0.1")
        self.client.get(reverse("auth_and_perms:remove_impostor"), {"all": 1})
        self.assertFalse(ImpostorLog.objects.get().active)

    def test_terminar_la_suplantacion_actual(self):
        self.suplantar(self.miembro)
        response = self.client.get(reverse("auth_and_perms:remove_impostor"))
        self.assertEqual(response.wsgi_request.user.pk, self.miembro.pk)
        self.assertFalse(ImpostorLog.objects.get().active)
        self.assertNotIn("impostor", self.client.session)


class ImpostorMiddlewareTest(EscenarioOrganizaciones):
    def test_sin_sesion_esta_mal_configurado(self):
        request = RequestFactory().get("/")
        with self.assertRaises(ImproperlyConfigured):
            ImpostorMiddleware(lambda r: None).process_request(request)


class ProfileLanguageMiddlewareTest(EscenarioOrganizaciones):
    def registro_pendiente(self, metodo):
        user = User.objects.create_user(f"registro-{metodo}")
        RegistrationUser.objects.create(
            user=user,
            registration_method=metodo,
            expired_date=now() + timedelta(days=1),
            organization_name="Nueva",
        )
        self.client.force_login(user)
        return user

    def test_registro_por_otp_sin_perfil_cierra_sesion(self):
        self.registro_pendiente(1)
        response = self.client.get(reverse("auth_and_perms:select_organization_by_user"))
        self.assertRedirects(response, reverse("index"), fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_registro_por_firma_sin_perfil_cierra_sesion(self):
        self.registro_pendiente(2)
        response = self.client.get(reverse("auth_and_perms:select_organization_by_user"))
        self.assertRedirects(response, reverse("index"), fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_sin_perfil_ni_registro_da_404(self):
        self.client.force_login(User.objects.create_user("huerfano"))
        response = self.client.get(reverse("auth_and_perms:select_organization_by_user"))
        self.assertNegado(response, 404)
