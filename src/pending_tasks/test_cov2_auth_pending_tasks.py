"""API de tareas pendientes vista desde la API navegable de DRF."""

from django.test import TestCase
from django.urls import reverse

from pending_tasks.tests import PendingTaskSetUpMixin


class ArchivarDesdeLaApiNavegableTest(PendingTaskSetUpMixin, TestCase):
    def test_archivar_terminadas_con_accept_html(self):
        """La API navegable arma el formulario con `get_serializer()`; `archive_finished`
        no está en el mapa de serializers y el respaldo debe ser una clase real."""
        response = self.client.post(
            reverse("pending_tasks:api-pending_tasks-archive-finished"), HTTP_ACCEPT="text/html"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"archived", response.content)
