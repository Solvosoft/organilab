from django.urls import reverse

from laboratory.models import ObjectFeatures, Object, Catalog, ShelfObject
from laboratory.tests.utils import BaseLaboratorySetUpTest
import json

class ObjectViewTest(BaseLaboratorySetUpTest):

    def test_objectview_create(self):
        total_obj = Object.objects.all().count()
        url = reverse("laboratory:objectview_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        data = {
            "name": "Ácido Clorhídrico",
            "features": [1],
            "code": "AC",
            "synonym": "Ácido",
            "is_public": True,
            "model": "AC2022",
            "serie": "Ácido 222",
            "plaque": "AC4300",
            "type": "1",
            "capacity":200,
            "capacity_measurement_unit": 64,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Object.objects.last().materialcapacity.capacity==200)
        self.assertEqual(total_obj+1, Object.objects.all().count())
        success_url = reverse("laboratory:objectview_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})+"?type_id=1"
        self.assertRedirects(response, success_url)

    def test_objectview_create_no_capacity(self):
        total_obj = Object.objects.all().count()
        url = reverse("laboratory:objectview_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        data = {
            "name": "Ácido Clorhídrico",
            "features": [1],
            "code": "AC",
            "synonym": "Ácido",
            "is_public": True,
            "model": "AC2022",
            "serie": "Ácido 222",
            "plaque": "AC4300",
            "type": "1",
            "capacity_measurement_unit": 64,
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(not hasattr(Object.objects.last(),'materialcapacity'))
        self.assertTrue(total_obj, Object.objects.all().count())
        self.assertContains(response, "This field is required.")

    def test_objectview_create_no_capacity_unit(self):
        total_obj = Object.objects.all().count()
        url = reverse("laboratory:objectview_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        data = {
            "name": "Ácido Clorhídrico",
            "features": [1],
            "code": "AC",
            "synonym": "Ácido",
            "is_public": True,
            "model": "AC2022",
            "serie": "Ácido 222",
            "plaque": "AC4300",
            "type": "1",
            "capacity": 200
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(not hasattr(Object.objects.last(),'materialcapacity'))
        self.assertTrue(total_obj, Object.objects.all().count())
        self.assertContains(response, "This field is required.")


    def test_objectview_create_no_material(self):
        total_obj = Object.objects.all().count()
        url = reverse("laboratory:objectview_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        data = {
            "name": "Ácido Clorhídrico",
            "features": [1],
            "code": "AC",
            "synonym": "Ácido",
            "is_public": True,
            "model": "AC2022",
            "serie": "Ácido 222",
            "plaque": "AC4300",
            "type": "2",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(not hasattr(Object.objects.last(),"materialcapacity"))
        self.assertTrue(total_obj<Object.objects.all().count())
        success_url = reverse("laboratory:objectview_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})+"?type_id=2"
        self.assertRedirects(response, success_url)

    def test_update_no_material(self):
        object = Object.objects.filter(type=0).first()
        self.assertFalse(hasattr(object,'materialcapacity'))
        url = reverse("laboratory:objectview_update", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": object.pk})
        data = {
            "name": "RA Paquete 100 gr",
            "features": [1],
            "code": "RA43",
            "synonym": "RA",
            "is_public": True,
            "model": "RA2022",
            "serie": "Reactive 008",
            "plaque": "RA4300",
            "type": "0",
        }
        response = self.client.post(url, data=data)
        new_object= Object.objects.filter(type=1).first()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(hasattr(object, 'materialcapacity'))
        self.assertFalse(hasattr(new_object, 'materialcapacity'))
        success_url = reverse("laboratory:objectview_list", kwargs={"org_pk": self.org.pk,
                                                                "lab_pk": self.lab.pk}) + "?type_id=0"
        self.assertRedirects(response, success_url)


