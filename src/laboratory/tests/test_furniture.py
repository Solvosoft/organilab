from django.urls import reverse

from laboratory.models import Shelf, Furniture, ShelfObject, LaboratoryRoom, ObjectFeatures, TranferObject, Provider
from laboratory.tests.utils import BaseLaboratorySetUpTest

class FurnitureViewTest(BaseLaboratorySetUpTest):

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
            "labroom": 1,
            "dataconfig": "[[], []]",
            "color": "#73879C"
        }
        response_post = self.client.post(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        success_url = reverse("laboratory:rooms_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response_post, success_url)

    def test_create_furniture(self):
        labroom = LaboratoryRoom.objects.first()
        data = {
            "name": "Mueble Esquinero",
            "type": 75,
        }
        url = reverse("laboratory:furniture_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "labroom": labroom.pk})
        response = self.client.post(url, data=data)
        furniture = Furniture.objects.last()
        success_url = reverse("laboratory:furniture_update", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": furniture.pk})
        self.assertRedirects(response, success_url)
        self.assertIn("Mueble Esquinero", list(Furniture.objects.values_list("name", flat=True)))

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

    def test_furniture_report_detail(self):
        data = {
            "pk": 1,
            "format": "pdf"
        }
        url = reverse("laboratory:reports_furniture_detail", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_add_furniture_type_catalog(self):
        url = reverse("laboratory:add_furniture_type_catalog")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

class ShelfViewTest(BaseLaboratorySetUpTest):

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
        self.assertEqual(response_post.status_code, 200)

    def test_create_shelf(self):
        data = {
            "shelf--name": "Muestras",
            "shelf--type": 72,
            "shelf--furniture": 1,
            "shelf--color": "#73879C",
            "shelf--col": 0,
            "shelf--row": 2,
            "shelf--discard": False,
            "shelf--quantity": 3,
            "shelf--description": "Estante de muestras",
            "shelf--measurement_unit": 59
        }
        url = reverse("laboratory:shelf_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIn("Muestras", list(Shelf.objects.values_list("name", flat=True)))
        self.assertEqual(response.status_code, 200)

    def test_delete_shelf(self):
        shelf = Shelf.objects.last()
        url = reverse("laboratory:shelf_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": shelf.pk,
                                                         "row": shelf.row(), "col": shelf.col()})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_add_shelf_type_catalog(self):
        url = reverse("laboratory:add_shelf_type_catalog")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_shelfs(self):
        transfer = TranferObject.objects.first()
        data = {
            "lab": self.lab.pk,
            "id": transfer.pk
        }
        url = reverse("laboratory:get_shelfs")
        response = self.client.post(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_edit_object(self):
        shelf_object = ShelfObject.objects.first()
        provider = Provider.objects.first()
        data = {
            "lab": self.lab.pk,
            "provider": provider.pk,
            "amount": 3,
            "shelf_object": shelf_object.pk,
            "options": 2
        }
        url = reverse("laboratory:edit_object", kwargs={"pk": self.lab.pk, })
        response = self.client.post(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

class ShelfObjectViewTest(BaseLaboratorySetUpTest):

    def test_get_shelfobject_list(self):
        url = reverse("laboratory:list_shelfobject", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_create_shelfobject(self):
        total = ShelfObject.objects.all().count()
        data = {
            "object": 1,
            "shelf": 1,
            "quantity": 5,
            "limit_quantity": 4,
            "measurement_unit": 63,
            "row": 0,
            "col": 1

        }
        url = reverse("laboratory:shelfobject_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(total+1, ShelfObject.objects.all().count())

    def test_delete_shelfobject(self):
        shelfobject = ShelfObject.objects.last()
        pk_check = shelfobject.pk
        url = reverse("laboratory:shelfobject_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": shelfobject.pk})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(pk_check, list(ShelfObject.objects.values_list("pk", flat=True)))

    def test_detail_shelfobject(self):
        shelf_object = ShelfObject.objects.first()
        url = reverse("laboratory:shelfobject_detail", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": shelf_object.pk})
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_searchupdate_shelfobject(self):
        shelf_object = ShelfObject.objects.first()
        url = reverse("laboratory:shelfobject_searchupdate", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": shelf_object.pk})
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_get_shelfobject_limit(self):
        shelf_object = ShelfObject.objects.first()
        url = reverse("laboratory:get_shelfobject_limit", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": shelf_object.pk})
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_shelfobject_report(self):
        url = reverse("laboratory:reports_shelf_objects", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk":1 })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_limited_shelf_objects_report(self):
        data = {
            "pk": 1,
            "format": "pdf"
        }
        url = reverse("laboratory:reports_limited_shelf_objects", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_limited_shelf_objects_list_report(self):
        url = reverse("laboratory:reports_limited_shelf_objects_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_object_detail(self):
        shelf_object = ShelfObject.objects.first()
        data = {
            "shelf_object": shelf_object.pk,
        }
        url = reverse("laboratory:get_object_detail")
        response = self.client.post(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_get_lab_id(self):
        url = reverse("laboratory:get_lab_id")
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

class ObjectFeaturesViewTest(BaseLaboratorySetUpTest):

    def test_update_objectfeature(self):
        objfeature = ObjectFeatures.objects.first()
        url = reverse("laboratory:object_feature_update", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": objfeature.pk})

        response_get = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "Es un reactivo en la industria química")

        data = {
            "name": "Reactivo 1",
            "description": "Es un reactivo en la industria química empacado en saco de 50kg o bolsas de 2kg."
        }
        response_post = self.client.post(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        success_url = reverse("laboratory:object_feature_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response_post.status_code, 302)
        self.assertRedirects(response_post, success_url)
        self.assertIn("Reactivo 1", list(ObjectFeatures.objects.values_list("name", flat=True)))

    def test_create_objectfeature(self):
        data = {
            "name": "Guantes",
            "description": "Brinda protección en manos y brazos a la hora de manipular cualquier material que lo requiera.",
        }
        url = reverse("laboratory:object_feature_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data)
        success_url = reverse("laboratory:object_feature_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, success_url)
        self.assertIn("Guantes", list(ObjectFeatures.objects.values_list("name", flat=True)))

    def test_delete_objectfeature(self):
        objfeature = ObjectFeatures.objects.first()
        url = reverse("laboratory:object_feature_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": objfeature.pk})
        response = self.client.post(url)
        success_url = reverse("laboratory:object_feature_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, success_url)

class ObjectViewTest(BaseLaboratorySetUpTest):

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

class TransferObjectViewTest(BaseLaboratorySetUpTest):

    def test_transfer_objects(self):
        url = reverse("laboratory:transfer_objects", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_update_transfer(self):
        transfer = TranferObject.objects.first()
        url = reverse("laboratory:update_transfer", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "transfer_pk": transfer.pk, "shelf_pk": 1, })
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_delete_transfer(self):
        transfer = TranferObject.objects.last()
        data = {
            "id": transfer.pk
        }
        url = reverse("laboratory:delete_transfer", kwargs={"pk": self.lab.pk, })
        response = self.client.post(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

class SustanceCharacteristicsViewTest(BaseLaboratorySetUpTest):

    def test_organizationreactivepresence(self):
        url = reverse("laboratory:organizationreactivepresence", kwargs={"org_pk": self.org.pk, })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_download_h_code_reports(self):
        url = reverse("laboratory:download_h_code_reports", kwargs={"org_pk": self.org.pk, })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_h_code_reports(self):
        url = reverse("laboratory:h_code_reports", kwargs={"org_pk": self.org.pk, })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)