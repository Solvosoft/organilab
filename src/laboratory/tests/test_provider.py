from django.urls import reverse

from laboratory.models import Provider
from laboratory.tests.utils import BaseLaboratorySetUpTest


class ProviderViewTest(BaseLaboratorySetUpTest):

    def test_provider_list(self):
        url = reverse(
            "laboratory:list_provider",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "LP Company")
        self.assertTemplateUsed(response, template_name="laboratory/provider_list.html")

    def test_udpate_provider(self):
        provider = Provider.objects.first()
        url = reverse(
            "laboratory:update_lab_provider",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": provider.pk},
        )
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "Karine Products")
        data = {
            "name": "Karine Chemicals Products",
            "phone_number": "(506)2209-2209",
            "email": "karinechemicalsproductos@cr.com",
            "legal_identity": "3-8764-8354",
            "laboratory": 1,
        }
        response_post = self.client.post(url, data=data)
        self.assertEqual(response_post.status_code, 302)
        success_url = reverse(
            "laboratory:list_provider",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        self.assertRedirects(response_post, success_url)
        self.assertIn(
            "Karine Chemicals Products",
            list(Provider.objects.values_list("name", flat=True)),
        )

    def test_add_provider(self):
        data = {
            "name": "NatVou",
            "phone_number": "(506)2240-8035",
            "email": "natvou@example.com",
            "legal_identity": "3-876-763",
            "laboratory": self.lab,
        }
        url = reverse(
            "laboratory:add_provider",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        response = self.client.post(url, data=data)
        success_url = reverse(
            "laboratory:list_provider",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        self.assertRedirects(response, success_url)
        self.assertIn("NatVou", list(Provider.objects.values_list("name", flat=True)))
