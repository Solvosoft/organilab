"""Edición del propio perfil y cambio de contraseña (`authentication/users.py`)."""

from django.contrib.auth.models import User
from django.urls import reverse

from auth_and_perms.tests.escenario import EscenarioOrganizaciones
from authentication.forms import CreateUserForm, PasswordChangeForm


class CambioDePerfilTest(EscenarioOrganizaciones):
    def setUp(self):
        self.usuario = self.crear_usuario(
            "duena", self.org_a, perms=["auth_and_perms.change_own_profile"], ambito="perfil"
        )
        self.victima = self.crear_usuario("victima", self.org_b, first_name="Original")
        self.client.force_login(self.usuario)

    def datos_formulario(self, username):
        return {
            "username": username,
            "first_name": "Cambiado",
            "last_name": "Apellido",
            "email": f"{username}@ejemplo.cr",
            "phone_number": "8888-8888",
            "language": "es",
            "job_position": "Regente",
            "identification": "1-1111-1111",
            "address": "San José",
            "workplace": [self.org_a.pk],
        }

    def test_editar_el_propio_perfil_guarda_usuario_y_perfil(self):
        url = reverse("laboratory:profile", args=[self.usuario.pk])
        response = self.client.post(url, data=self.datos_formulario("duena"))
        self.assertRedirects(
            response, reverse("laboratory:profile", args=[self.usuario.pk]), fetch_redirect_response=False
        )
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.first_name, "Cambiado")
        self.assertEqual(self.usuario.profile.job_position, "Regente")
        self.assertEqual(list(self.usuario.profile.workplace.all()), [self.org_a])

    def test_ver_el_perfil_de_otro_usuario_da_404(self):
        response = self.client.get(reverse("laboratory:profile", args=[self.victima.pk]))
        self.assertNegado(response, 404)

    def test_post_sobre_el_perfil_de_otro_usuario_no_lo_modifica(self):
        """Antes la vista guardaba el formulario y solo después respondía 404."""
        response = self.client.post(
            reverse("laboratory:profile", args=[self.victima.pk]),
            data=self.datos_formulario("victima-tomada"),
        )
        self.assertNegado(response, 404)
        self.victima.refresh_from_db()
        self.assertEqual(self.victima.username, "victima")
        self.assertEqual(self.victima.first_name, "Original")

    def test_cambio_de_contrasena_con_errores_devuelve_los_errores(self):
        response = self.client.post(
            reverse("laboratory:password_change", args=[self.usuario.pk]),
            data={"password": "UnaClaveLarga#2024", "password_confirm": "OtraClave#2024"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("password_confirm", response.json()["errors"])

    def test_cambio_de_contrasena_de_otro_usuario_da_404(self):
        response = self.client.post(
            reverse("laboratory:password_change", args=[self.victima.pk]),
            data={"password": "UnaClaveLarga#2024", "password_confirm": "UnaClaveLarga#2024"},
        )
        self.assertNegado(response, 404)
        self.victima.refresh_from_db()
        self.assertTrue(self.victima.check_password("clave-segura-123"))


class FormulariosDeAutenticacionTest(EscenarioOrganizaciones):
    def test_crear_usuario_con_correo_ya_registrado_es_invalido(self):
        User.objects.create_user("repetido@ejemplo.cr")
        form = CreateUserForm(
            data={
                "first_name": "Ana",
                "last_name": "Mora",
                "email": "repetido@ejemplo.cr",
                "user_type": 3,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_contrasenas_distintas_son_invalidas(self):
        form = PasswordChangeForm(
            data={"password": "UnaClaveLarga#2024", "password_confirm": "Distinta#2024"}
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()["password_confirm"][0].code, "password_mismatch")
