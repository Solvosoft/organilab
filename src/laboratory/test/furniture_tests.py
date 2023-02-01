from django.urls import reverse

from laboratory.models import Shelf, Furniture, ShelfObject
from laboratory.test.utils import BaseSetUpTest


class FurnitureViewTest(BaseSetUpTest):

    def test_get_furniture_list(self):
        url = reverse("laboratory:furniture_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_update_furniture(self):
        furniture = Furniture.objects.first()
        url = reverse("laboratory:furniture_update", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": furniture.pk})

        #Checking by method get if initial data furniture exists
        response_get = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "Mueble 1")

        # Updating furniture
        data = {
            "name": "Mueble Aéreo",
            "type": 75,
        }
        response_post = self.client.post(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        success_url = reverse("laboratory:rooms_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response_post, success_url)

    def test_create_furniture(self):
        data = {
            "name": "Mueble Esquinero",
            "type": 75,
        }
        url = reverse("laboratory:furniture_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data)
        success_url = reverse("laboratory:rooms_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response, success_url)
        self.assertIn("Estante de muestras", list(Furniture.objects.values_list("name", flat=True)))

    def test_delete_furniture(self):
        furniture = Furniture.objects.last()
        url = reverse("laboratory:furniture_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": furniture.pk})
        response = self.client.post(url)
        success_url = reverse("laboratory:rooms_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, success_url)

class ShelfViewTest(BaseSetUpTest):

    def test_get_shelf_list(self):
        data = {
            'furniture': 1
        }
        url = reverse("laboratory:list_shelf", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_update_shelf(self):
        shelf = Shelf.objects.first()
        url = reverse("laboratory:shelf_edit", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": shelf.pk,
                                                       "row": shelf.row(), "col": shelf.col()})

        #Checking by method get if initial data shelf exists
        response_get = self.client.get(url, data={'furniture': shelf.furniture.pk}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "Primer Estante")

        # Updating shelf
        data = {
            "name": "Estante central",
            "type": 74,
            "furniture": 1,
            "color": "#73879C",
            "row": 1,
            "col": 0
        }
        response_post = self.client.post(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
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
        shelf = Shelf.objects.first()
        url = reverse("laboratory:shelf_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": shelf.pk,
                                                         "row": shelf.row(), "col": shelf.col()})
        response = self.client.post(url)
        success_url = reverse("laboratory:list_shelf", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, success_url)

class ShelfObjectViewTest(BaseSetUpTest):

    def test_get_shelfobject_list(self):
        url = reverse("laboratory:list_shelfobject", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_update_shelf(self):
        shelfobject = ShelfObject.objects.first()
        url = reverse("laboratory:shelfobject_edit", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": shelfobject.pk})

        #Checking by method get if initial data shelfobject exists
        response_get = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "")

        # Updating shelfobject
        data = {
            "object": 1
        }
        response_post = self.client.post(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        success_url = reverse("laboratory:list_shelfobject", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response_post, success_url)

    def test_create_shelf(self):
        data = {
            "object": 1
        }
        url = reverse("laboratory:shelfobject_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data)
        success_url = reverse("laboratory:list_shelfobject", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response, success_url)
        self.assertIn("", list(ShelfObject.objects.values_list("object", flat=True)))

    def test_delete_shelfobject(self):
        shelfobject = ShelfObject.objects.first()
        url = reverse("laboratory:shelf_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": shelfobject.pk})
        response = self.client.post(url)
        success_url = reverse("laboratory:list_shelfobject", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, success_url)
