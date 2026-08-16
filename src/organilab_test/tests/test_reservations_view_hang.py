# -*- coding: utf-8 -*-
"""Las vistas de las pruebas Selenium de cap5 responden sin navegador.

Las pruebas de reservaciones fallan porque la petición nunca llega a
completarse en Chrome, ni siquiera con 180 s de espera. Esto acota el
problema: si estas vistas responden aquí en milisegundos, el bloqueo no está
en la aplicación sino en la infraestructura de Selenium.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class ReservationsViewsRespondTest(TestCase):
    fixtures = ["selenium/capacitacion.json"]

    def _get_as(self, user_pk, url):
        self.client.force_login(User.objects.get(pk=user_pk))
        return self.client.get(url)

    def test_reservations_list_responds(self):
        response = self._get_as(
            2,
            reverse(
                "reservations_management:reservations_list",
                kwargs={"org_pk": 4, "status": 0},
            ),
        )
        self.assertEqual(response.status_code, 200)

    def test_my_reservations_redirects_without_permission(self):
        # El docente no tiene permiso sobre las reservaciones del laboratorio:
        # la vista redirige al aviso de error, no revienta ni se cuelga.
        response = self._get_as(
            4, reverse("laboratory:my_reservations", kwargs={"org_pk": 4, "lab_pk": 1})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("error", response["Location"])

    def test_my_labs_responds_for_student(self):
        response = self._get_as(
            5, reverse("laboratory:mylabs", kwargs={"org_pk": 4})
        )
        self.assertEqual(response.status_code, 200)
