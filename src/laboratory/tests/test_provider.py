from django.urls import reverse

from laboratory.models import Provider
from laboratory.tests.utils import BaseLaboratorySetUpTest


class ProviderViewTest(BaseLaboratorySetUpTest):

    def test_provider_list(self):
        url = reverse(
            "laboratory:provider_view",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_udpate_provider(self):
        url = reverse(
            "laboratory:api-provider-list",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        data = {
            "name": "Karine Chemicals Products",
            "phone_number": "(506)2209-2209",
            "email": "karinechemicalsproductos@cr.com",
            "legal_identity": "3-8764-8354",
            "laboratory": self.lab.pk,
        }

        response = self.client.post(url, data=data, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Provider.objects.filter(name=data["name"]).exists())

    def test_delete_provider(self):
        url = reverse(
            "laboratory:api-provider-detail",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": 2},
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Provider.objects.filter(pk=2).exists())

    def test_add_provider(self):
        url = reverse(
            "laboratory:api-provider-list",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        data = {
            "name": "NatVou",
            "phone_number": "(506)2240-8035",
            "email": "natvou@example.com",
            "legal_identity": "3-876-763",
            "laboratory_id": self.lab.pk,
        }

        response = self.client.post(url, data=data, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Provider.objects.filter(name=data["name"]).exists())
