import json

from django.test import tag
from django.urls import reverse

from laboratory.models import LaboratoryProcess
from laboratory.tests.gtapi.base import TestCaseBase


class LaboratoryProcessApiTest(TestCaseBase):
    """API de procesos de laboratorio.

    Sirve además para separar responsabilidades cuando el flujo Selenium de
    `laboratory_process_list` falla: si estas pruebas pasan, el problema está en
    el navegador (el editor TinyMCE dentro del modal) y no en el backend.
    """

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user1)
        self.org_pk = self.org1.pk
        self.lab_pk = self.lab1_org1.pk

    @property
    def list_url(self):
        return reverse(
            "laboratory:api-laboratory-process-list",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab_pk},
        )

    def test_create_requires_description(self):
        response = self.client.post(
            self.list_url,
            data=json.dumps({"laboratory": self.lab_pk}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("description", response.json())

    def test_create_and_list(self):
        response = self.client.post(
            self.list_url,
            data=json.dumps(
                {"laboratory": self.lab_pk, "description": "<p>Proceso</p>"}
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content[:400])
        self.assertTrue(
            LaboratoryProcess.objects.filter(laboratory=self.lab_pk).exists()
        )
