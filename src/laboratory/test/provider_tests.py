from django.urls import reverse

from laboratory.models import Provider
from laboratory.test.utils import BaseSetUpTest


class ProviderViewTest(BaseSetUpTest):


    def test_get_provider_list(self):
        url = reverse("laboratory:list_provider", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


    def test_get_provider_detail(self):
        url = reverse("laboratory:update_lab_provider", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Karine Products")


    def test_post_provider(self):
        data = {
            "name": "NatVou",
            "phone_number": "(506)2240-8035",
            "email": "natvou@example.com",
            "legal_identity": "3-876-763",
            "laboratory": self.lab
        }
        url = reverse("laboratory:add_provider", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data)
        success_url = reverse("laboratory:list_provider", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response, success_url)
        self.assertIn("NatVou", list(Provider.objects.values_list("name", flat=True)))
