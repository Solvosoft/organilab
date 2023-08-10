from django.urls import reverse

from laboratory.models import Object, ShelfObject, MaterialCapacity, Catalog, \
    ObjectFeatures
from laboratory.tests.utils import BaseLaboratorySetUpTest
import json
from django.utils.translation import gettext_lazy as _


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

    def test_objectview_create_capacity_str(self):
        total_obj = Object.objects.all().count()
        url = reverse("laboratory:objectview_create",
                      kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
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
            "capacity": "RAF",
            "capacity_measurement_unit": 64
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(not hasattr(Object.objects.last(), 'materialcapacity'))
        self.assertTrue(total_obj, Object.objects.all().count())
        self.assertContains(response, "<li>Enter a number.</li>")

    def test_objectview_create_capacity_negative(self):
        total_obj = Object.objects.all().count()
        url = reverse("laboratory:objectview_create",
                      kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
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
            "capacity": -200,
            "capacity_measurement_unit": 64
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(not hasattr(Object.objects.last(), 'materialcapacity'))
        self.assertTrue(total_obj, Object.objects.all().count())
        self.assertContains(response, "<li>Enter a number.</li>")

    def test_objectview_create_no_unit(self):
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
            "capacity": 21.54,
            "capacity_measurement_unit": 27
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(not hasattr(Object.objects.last(),'materialcapacity'))
        self.assertTrue(total_obj, Object.objects.all().count())
        self.assertContains(response, "<li>Select a valid choice. That choice is not one of the available choices.</li>")

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

    def test_update_no_material_with_capacity_unit(self):
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
            "capacity": 21.54,
            "capacity_measurement_unit": 64
        }
        response = self.client.post(url, data=data)
        new_object= Object.objects.filter(type=1).first()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(hasattr(object, 'materialcapacity'))
        self.assertFalse(hasattr(new_object, 'materialcapacity'))
        success_url = reverse("laboratory:objectview_list", kwargs={"org_pk": self.org.pk,
                                                                "lab_pk": self.lab.pk}) + "?type_id=0"
        self.assertRedirects(response, success_url)

    def test_create_shelfobject_material(self):

        material_data = {
            "name": "Ácido Clorhídrico",
            "code": "AC",
            "synonym": "Ácido",
            "is_public": True,
            "model": "AC2022",
            "serie": "Ácido 222",
            "plaque": "AC4300",
            "type": "1",
            "organization": self.org
        }
        material = Object.objects.create(**material_data)
        material.features.add(ObjectFeatures.objects.get(pk=1))

        unit = Catalog.objects.get(pk=59)
        MaterialCapacity.objects.create(
            object=material,
            capacity=200,
            capacity_measurement_unit=unit
        )
        data = {
            "shelf": 13,
            "object": material.pk,
            "objecttype": 1,
            "status": 1,
            "quantity": 23.0,
            "limit_quantity": 7.0,
            "in_where_laboratory": 1,
            "marked_as_discard": False,
            "minimum_limit": 0,
            "maximum_limit": 0,
        }
        url = reverse("laboratory:api-shelfobject-create-shelfobject",
                      kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.client.post(url, data=data, content_type='application/json')
        shelfobject_count = ShelfObject.objects.filter(shelf__pk=13).count()
        new_shelobject = ShelfObject.objects.last()
        data = {
                "shelf": 13,
                "object": 2,
                "batch": 2,
                "objecttype": 0,
                "status": 1,
                "quantity": 10.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": 1,
                "course_name": "A reactive product",
                "measurement_unit": 59,
                "marked_as_discard": False,
                "minimum_limit": 0,
                "maximum_limit": 0,
                "container": new_shelobject.pk
            }
        response=self.client.post(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(ShelfObject.objects.filter(shelf__pk=13).count()>shelfobject_count)

    def test_create_shelfobject_material_over_capacity(self):

        material_data = {
            "name": "Ácido Clorhídrico",
            "code": "AC",
            "synonym": "Ácido",
            "is_public": True,
            "model": "AC2022",
            "serie": "Ácido 222",
            "plaque": "AC4300",
            "type": "1",
            "organization": self.org
        }
        material = Object.objects.create(**material_data)
        material.features.add(ObjectFeatures.objects.get(pk=1))

        unit = Catalog.objects.get(pk=59)
        MaterialCapacity.objects.create(
            object=material,
            capacity=200,
            capacity_measurement_unit=unit
        )
        data = {
            "shelf": 13,
            "object": material.pk,
            "objecttype": 1,
            "status": 1,
            "quantity": 23.0,
            "limit_quantity": 7.0,
            "in_where_laboratory": 1,
            "marked_as_discard": False,
            "minimum_limit": 0,
            "maximum_limit": 0,
        }
        url = reverse("laboratory:api-shelfobject-create-shelfobject",
                      kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.client.post(url, data=data, content_type='application/json')
        shelfobject_count = ShelfObject.objects.filter(shelf__pk=13).count()
        new_shelobject = ShelfObject.objects.last()
        data = {
                "shelf": 13,
                "object": 2,
                "batch": 2,
                "objecttype": 0,
                "status": 1,
                "quantity": 201.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": 1,
                "course_name": "A reactive product",
                "measurement_unit": 59,
                "marked_as_discard": False,
                "minimum_limit": 0,
                "maximum_limit": 0,
                "container": new_shelobject.pk
            }
        response=self.client.post(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(json.loads(response.content)['errors']['quantity'][0]=="Quantity cannot be greater than the container capacity limit: 200.0.")
        self.assertTrue(ShelfObject.objects.filter(shelf__pk=13).count()==shelfobject_count)


    def test_create_shelfobject_material_other_capacity_unit(self):

        material_data = {
            "name": "Ácido Clorhídrico",
            "code": "AC",
            "synonym": "Ácido",
            "is_public": True,
            "model": "AC2022",
            "serie": "Ácido 222",
            "plaque": "AC4300",
            "type": "1",
            "organization": self.org
        }
        material = Object.objects.create(**material_data)
        material.features.add(ObjectFeatures.objects.get(pk=1))

        unit = Catalog.objects.get(pk=64)
        MaterialCapacity.objects.create(
            object=material,
            capacity=200,
            capacity_measurement_unit=unit
        )
        data = {
            "shelf": 13,
            "object": material.pk,
            "objecttype": 1,
            "status": 1,
            "quantity": 23.0,
            "limit_quantity": 7.0,
            "in_where_laboratory": 1,
            "marked_as_discard": False,
            "minimum_limit": 0,
            "maximum_limit": 0,
        }
        url = reverse("laboratory:api-shelfobject-create-shelfobject",
                      kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.client.post(url, data=data, content_type='application/json')
        shelfobject_count = ShelfObject.objects.filter(shelf__pk=13).count()
        new_shelobject = ShelfObject.objects.last()
        data = {
                "shelf": 13,
                "object": 2,
                "batch": 2,
                "objecttype": 0,
                "status": 1,
                "quantity": 30.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": 1,
                "course_name": "A reactive product",
                "measurement_unit": 59,
                "marked_as_discard": False,
                "minimum_limit": 0,
                "maximum_limit": 0,
                "container": new_shelobject.pk
            }
        response=self.client.post(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(json.loads(response.content)['errors']['measurement_unit'][0]=="Measurement unit cannot be different than the container object measurement unit: Unidades.")
        self.assertTrue(ShelfObject.objects.filter(shelf__pk=13).count()==shelfobject_count)

