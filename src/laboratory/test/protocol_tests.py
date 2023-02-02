from django.urls import reverse

from laboratory.models import Protocol
from laboratory.test.utils import BaseSetUpTest


class ProtocolViewTest(BaseSetUpTest):

    def test_get_protocol_list(self):
        url = reverse("laboratory:protocol_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_protocol(self):
        url = reverse("laboratory:protocol_update", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": 1})

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
            "file": self.chfile.upload_id,
        }
        url = reverse("laboratory:protocol_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data)
        success_url = reverse("laboratory:protocol_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response, success_url)
        self.assertIn("Manejo de desechos", list(Protocol.objects.values_list("name", flat=True)))

    def test_delete_protocol(self):
        url = reverse("laboratory:protocol_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": 1})
        response = self.client.post(url)
        success_url = reverse("laboratory:protocol_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, success_url)
