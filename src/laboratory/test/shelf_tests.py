from django.urls import reverse

from laboratory.models import Shelf
from laboratory.test.utils import BaseSetUpTest


class ShelfViewTest(BaseSetUpTest):

    def test_get_shelf_list(self):
        url = reverse("laboratory:list_shelf", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_shelf(self):
        url = reverse("laboratory:shelf_edit", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": 1})

        # Checking by method get if initial data shelf exists
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "Primer Estante")

        # Updating shelf
        data = {
            "name": "Estante central",
            "type": 74,
            "color": "#73879C"
        }
        response_post = self.client.post(url, data=data)
        success_url = reverse("laboratory:list_shelf", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response_post, success_url)

    def test_create_shelf(self):
        data = {
            "name": "Estante de muestras",
            "type": 74,
            "color": "#73879C"
        }
        url = reverse("laboratory:shelf_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data)
        success_url = reverse("laboratory:list_shelf", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response, success_url)
        self.assertIn("Estante de muestras", list(Shelf.objects.values_list("name", flat=True)))

    def test_delete_shelf(self):
        url = reverse("laboratory:shelf_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": 1})
        response = self.client.post(url)
        success_url = reverse("laboratory:list_shelf", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, success_url)
