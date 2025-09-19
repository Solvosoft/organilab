from django.urls import reverse

from laboratory.models import (
    Object,
    ShelfObject,
    MaterialCapacity,
    Catalog,
    ObjectFeatures,
)
from laboratory.tests.utils import BaseLaboratorySetUpTest
import json
from django.utils.translation import gettext_lazy as _


class ObjectViewTest(BaseLaboratorySetUpTest):

    def test_objectview_create(self):
        """
        Test for object view when create a material object with capacitymaterial
        """
        total_obj = Object.objects.all().count()
        url = reverse(
            "laboratory:objectview_create",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
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
            "is_container": True,
            "capacity": 200,
            "capacity_measurement_unit": 64,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(MaterialCapacity.objects.last().capacity == 200)
        self.assertEqual(total_obj + 1, Object.objects.all().count())
        success_url = (
            reverse(
                "laboratory:objectview_list",
                kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
            )
            + "?type_id=1"
        )
        self.assertRedirects(response, success_url)

    def test_objectview_create_no_capacity(self):
        """
        Test for object view when create an material object without capacity and send a
        error because the capacity is required when the object is a material
        """

        total_obj = Object.objects.all().count()
        url = reverse(
            "laboratory:objectview_create",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
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
            "is_container": True,
            "capacity_measurement_unit": 64,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(not hasattr(Object.objects.last(), "materialcapacity"))
        self.assertTrue(total_obj, Object.objects.all().count())
        self.assertContains(response, "This field is required.")

    def test_objectview_create_no_capacity_unit(self):
        """
        Test for object view when create ax material object without capacity_unit and send a
        error because the capacity_unit is required when the object is a material
        """
        total_obj = Object.objects.all().count()
        url = reverse(
            "laboratory:objectview_create",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
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
            "is_container": True,
            "capacity": 200,
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(total_obj, Object.objects.all().count())
        self.assertContains(response, "This field is required.")

    def test_objectview_create_capacity_str(self):
        """
        Test for object view when create a material object with the data of capacity is
        string and this field need a number.
        """
        total_obj = Object.objects.all().count()
        url = reverse(
            "laboratory:objectview_create",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
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
            "capacity_measurement_unit": 64,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(total_obj, Object.objects.all().count())
        self.assertContains(response, "<li>Enter a number.</li>")

    def test_objectview_create_capacity_negative(self):
        """
        Test for object view when create a material object with the data of capacity is
        negative number and this field need a positive number.
        """
        total_obj = Object.objects.all().count()
        url = reverse(
            "laboratory:objectview_create",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
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
            "capacity_measurement_unit": 64,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(total_obj, Object.objects.all().count())
        self.assertContains(
            response, "<li>Ensure this value is greater than or equal to 1e-07.</li>"
        )

    def test_objectview_create_no_unit(self):
        """
        Test for object view when create a material object with capacity_unit is
        a option that the field do not accept because only permit a option from
        Catalog model with the key units.
        """
        total_obj = Object.objects.all().count()
        url = reverse(
            "laboratory:objectview_create",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
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
            "capacity_measurement_unit": 27,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(total_obj, Object.objects.all().count())
        self.assertContains(
            response,
            "<li>Select a valid choice. That choice is not one of the available choices.</li>",
        )

    def test_objectview_create_no_material(self):
        """
        Test for object view when create an object that is not of material type, because
        the capacity and capacity unit not is required
        """
        total_obj = Object.objects.all().count()
        url = reverse(
            "laboratory:objectview_create",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
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
        self.assertTrue(not hasattr(Object.objects.last(), "materialcapacity"))
        self.assertTrue(total_obj < Object.objects.all().count())
        success_url = (
            reverse(
                "laboratory:objectview_list",
                kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
            )
            + "?type_id=2"
        )
        self.assertRedirects(response, success_url)

    def test_update_no_material(self):
        """
        Test for object view when update an  object that is not of material type, because
        the capacity and capacity unit not is required
        """
        object = Object.objects.filter(type=0).first()
        self.assertFalse(hasattr(object, "materialcapacity"))
        url = reverse(
            "laboratory:objectview_update",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": object.pk},
        )
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
        new_object = Object.objects.filter(type=1).first()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(hasattr(object, "materialcapacity"))
        self.assertFalse(hasattr(new_object, "materialcapacity"))
        success_url = (
            reverse(
                "laboratory:objectview_list",
                kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
            )
            + "?type_id=0"
        )
        self.assertRedirects(response, success_url)

    def test_update_no_material_with_capacity_unit(self):
        """
        Test for object view when update an  object that is not of material type, because
        the capacity and capacity unit not is required
        """
        object = Object.objects.filter(type=0).first()
        self.assertFalse(hasattr(object, "materialcapacity"))
        url = reverse(
            "laboratory:objectview_update",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": object.pk},
        )
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
            "capacity_measurement_unit": 64,
        }
        response = self.client.post(url, data=data)
        new_object = Object.objects.filter(type=1).first()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(hasattr(object, "materialcapacity"))
        self.assertFalse(hasattr(new_object, "materialcapacity"))
        """In objects different of material type the material capacity not create"""
        success_url = (
            reverse(
                "laboratory:objectview_list",
                kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
            )
            + "?type_id=0"
        )
        self.assertRedirects(response, success_url)

    def test_update_material(self):
        """
        Test for object view when update an  object that is material type, but update
        the field is_container to False and the object a shelfobject used as a container
        """
        object = Object.objects.get(pk=4)
        self.assertFalse(hasattr(object, "materialcapacity"))
        url = (
            reverse(
                "laboratory:objectview_update",
                kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": object.pk},
            )
            + "?type_id=1"
        )
        data = {
            "name": "RA Paquete 100 gr",
            "features": [1],
            "code": "RA43",
            "synonym": "RA",
            "is_public": True,
            "model": "RA2022",
            "serie": "Reactive 008",
            "plaque": "RA4300",
            "type": "1",
            "is_container": False,
        }
        response = self.client.post(url, data=data)
        new_object = Object.objects.get(pk=4)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(hasattr(object, "materialcapacity"))
        self.assertFalse(hasattr(new_object, "materialcapacity"))
        self.assertContains(
            response,
            "<li>This field cannot be updated because the material is used as a container for at least one reactive.</li>",
        )
