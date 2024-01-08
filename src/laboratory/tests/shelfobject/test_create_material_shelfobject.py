from django.contrib.contenttypes.models import ContentType
from auth_and_perms.models import Rol, ProfilePermission
from laboratory.models import Laboratory, ShelfObject, Catalog, UserOrganization, \
    OrganizationStructure, Object, ObjectFeatures, MaterialCapacity
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
import json
class CreateShelfobjectTest(TestCase):
    fixtures = ["laboratory_data.json"]

    def setUp(self):
        super().setUp()

        self.client = Client()
        self.user = User.objects.get(pk=2)
        self.user1 = User.objects.get(pk=3)
        self.org_pk = 1
        self.org = OrganizationStructure.objects.get(pk=1)
        self.lab = Laboratory.objects.first()
        create_status_rol = Rol.objects.create(name="Test create shelfobject", color="#FFF")
        permission = Permission.objects.filter(codename="add_shelfobject")
        create_status_rol.permissions.add(*permission)
        profile_permission = ProfilePermission.objects.create(profile=self.user.profile,
                                                              object_id=1,
                                                              content_type=ContentType.objects.get(
                                                                  app_label='laboratory',
                                                                  model='organizationstructure')
                                                              )
        profile_permission.rol.add(create_status_rol)
        org = OrganizationStructure.objects.get(pk=1)
        user_org = UserOrganization.objects.create(organization=org, user=self.user, type_in_organization=1
                                                   )
        org.users.add(self.user)
        self.client.force_login(self.user)
        self.material= ShelfObject.objects.get(pk=6)

    def test_create_shelfobject_material(self):
        """
        Test for API create_shelfobject when the objecttype is 1 and all the data is given correctly
        """
        material_data = {
            "name": "Ácido Clorhídrico",
            "code": "AC",
            "synonym": "Ácido",
            "is_public": True,
            "model": "AC2022",
            "serie": "Ácido 222",
            "plaque": "AC4300",
            "type": "1",
            "organization": self.org,
            "is_container": True
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
                "maximum_limit": 40,
                "container_select_option": "clone",
                "container_for_cloning":material.id,
                "available_container":""
            }
        response=self.client.post(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(ShelfObject.objects.filter(shelf__pk=13).count()>shelfobject_count)

    def test_create_shelfobject_material_over_capacity(self):
        """
        Test for API create_shelfobject when the objecttype is 0 and all the data is
        given correctly.
        Also validate if the quantity of the shelfobject is bigger than the capacity of
        the container if is biggest send an error message
        """
        material_data = {
            "name": "Ácido Clorhídrico",
            "code": "AC",
            "synonym": "Ácido",
            "is_public": True,
            "model": "AC2022",
            "serie": "Ácido 222",
            "plaque": "AC4300",
            "type": "1",
            "organization": self.org,
            "is_container":True
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
                "container_select_option": "clone",
                "container_for_cloning":material.id,
                "available_container":""
        }
        response=self.client.post(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(json.loads(response.content)['errors']['quantity'][0]=="Quantity cannot be greater than the container capacity limit: 200.0.")
        self.assertTrue(ShelfObject.objects.filter(shelf__pk=13).count()==shelfobject_count)


    def test_create_shelfobject_material_other_capacity_unit(self):
        """
        Test for API create_shelfobject when the objecttype is 0 and all the data is
        given correctly.
        Also validate if the unit of the shelfobject that not is equals than the
        capacity unit of the container send an error message
        """
        material_data = {
            "name": "Ácido Clorhídrico",
            "code": "AC",
            "synonym": "Ácido",
            "is_public": True,
            "model": "AC2022",
            "serie": "Ácido 222",
            "plaque": "AC4300",
            "type": "1",
            "organization": self.org,
            "is_container": True,
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
                "container_select_option": "clone",
                "container_for_cloning":material.id,
                "available_container":""
            }
        response=self.client.post(url, data=data, content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertTrue(json.loads(response.content)['errors']['measurement_unit'][0]=="Measurement unit cannot be different than the container object measurement unit: Unidades.")
        self.assertTrue(ShelfObject.objects.filter(shelf__pk=13).count()==shelfobject_count)

