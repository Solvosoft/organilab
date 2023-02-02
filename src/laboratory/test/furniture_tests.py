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

    def test_furniture_report(self):
        data = {
            "pk": 1,
            "format": "pdf"
        }
        url = reverse("laboratory:reports_furniture", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_reactive_precursor_objects_report(self):
        data = {
            "all_labs": 2,
            "format": "pdf"
        }
        url = reverse("laboratory:reports_reactive_precursor_objects", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_add_furniture_type_catalog(self):
        url = reverse("laboratory:add_furniture_type_catalog", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

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

    def test_add_shelf_type_catalog(self):
        url = reverse("laboratory:add_shelf_type_catalog", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

class ShelfObjectViewTest(BaseSetUpTest):

    def test_get_shelfobject_list(self):
        url = reverse("laboratory:list_shelfobject", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_update_shelfobject(self):
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

    def test_create_shelfobject(self):
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
        url = reverse("laboratory:shelfobject_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": shelfobject.pk})
        response = self.client.post(url)
        success_url = reverse("laboratory:list_shelfobject", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, success_url)

    def test_detail_shelfobject(self):
        url = reverse("laboratory:shelfobject_detail", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_searchupdate_shelfobject(self):
        url = reverse("laboratory:shelfobject_searchupdate", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_transfer_objects(self):
        url = reverse("laboratory:transfer_objects", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_get_shelfobject_limit(self):
        url = reverse("laboratory:get_shelfobject_limit", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_shelfobject_report(self):
        data = {
            "pk": 1,
        }
        url = reverse("laboratory:reports_shelf_objects", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_limited_shelf_objects_report(self):
        data = {
            "pk": 1,
            "format": "pdf"
        }
        url = reverse("laboratory:reports_limited_shelf_objects", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_reactive_precursor_objects_report(self):
        url = reverse("laboratory:reports_reactive_precursor_objects", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_limited_shelf_objects_list_report(self):
        url = reverse("laboratory:reports_limited_shelf_objects_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

class ObjectViewTest(BaseSetUpTest):

    def test_object_report(self):
        data = {
            "type_id": "1",
            "format": "pdf",
            "pk": 1
        }
        url = reverse("laboratory:reports_objects", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_objects_list_report(self):
        data = {
            "type_id": "1"
        }
        url = reverse("laboratory:reports_objects_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_reactive_precursor_object_list_report(self):
        url = reverse("laboratory:reactive_precursor_object_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_object_change_logs_report(self):

        url = reverse("laboratory:object_change_logs", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_precursor_report(self):
        data = {
            "consecutive": 1,
            "month": 2,
            "year": 2018
        }
        url = reverse("laboratory:precursor_report", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)