from django.urls import reverse

from laboratory.models import Protocol
from laboratory.tests.utils import BaseLaboratorySetUpTest
import json

class ProtocolViewTest(BaseLaboratorySetUpTest):

    def test_protocol_list(self):
        #This view is just a container(table), protocol table loads by "laboratory:api-protocol-list"
        url = reverse("laboratory:protocol_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template_name="laboratory/protocol/protocol_list.html")

    def test_update_protocol(self):
        protocol = Protocol.objects.get(name="Lavado de manos")
        url = reverse("laboratory:protocol_update", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": protocol.pk})

        # Checking by method get if initial data protocol exists
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "Lavado de manos")

        # Updating protocol
        data = {
            "name": "Lavado de manos",
            "short_description": "Higienización de las manos previa al ingreso del laboratorio y manipulación de los instrumentos del mismo.",
            "file": self.chfile.upload_id,
            "laboratory": self.lab
        }
        response_post = self.client.post(url, data=data)
        success_url = reverse("laboratory:protocol_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response_post, success_url)

    def test_create_protocol(self):
        data = {
            "name": "Manejo de desechos",
            "short_description": "Manipulación de desechos ordinarios y reciclables y su destino.",
            "file": self.chfile.upload_id
        }
        url = reverse("laboratory:protocol_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data)
        success_url = reverse("laboratory:protocol_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response, success_url)
        self.assertIn("Manejo de desechos", list(Protocol.objects.values_list("name", flat=True)))

    def test_delete_protocol(self):
        protocol = Protocol.objects.get(name="Manipulación de instrumentos de laboratorio")
        url = reverse("laboratory:protocol_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": protocol.pk})
        response = self.client.post(url)
        success_url = reverse("laboratory:protocol_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, success_url)
        self.assertNotIn("Manipulación de instrumentos de laboratorio", list(Protocol.objects.values_list("name", flat=True)))

    def test_api_protocol_list_set_limit(self):
        url = reverse("laboratory:api-protocol-list")
        response = self.client.get(url, data={"org_pk": self.org.pk, "lab_pk": self.lab.pk, 'offset': 0, 'limit': 10})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Control de plagas")

    def test_api_protocol_list_default_limit(self):
        url = reverse("laboratory:api-protocol-list")
        response = self.client.get(url, data={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Control de plagas", response.content.decode())
