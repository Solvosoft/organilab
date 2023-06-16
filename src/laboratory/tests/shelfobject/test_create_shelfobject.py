from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from auth_and_perms.models import Rol, ProfilePermission
from laboratory.models import Laboratory, ShelfObjectObservation, ShelfObject, Catalog, UserOrganization, \
    OrganizationStructure, Shelf, Object
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.utils.translation import gettext_lazy as _
import json

class CreateShelfobjectTest(TestCase):
    fixtures = ["laboratory_data.json"]

    def setUp(self):
        super().setUp()

        self.client = Client()
        self.user = User.objects.get(pk=2)
        self.user1 = User.objects.get(pk=3)
        self.org_pk = 1
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
        Example objecttype represents: 0)Reactive. 1)Material. 2)Equipment
        """
        data = {
                "shelf": 13,
                "object": 1,
                "objecttype": 1,
                "status": 1,
                "quantity": 23.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": 1,
                "measurement_unit": 59,
                "course_name": "A reactive product",
                "marked_as_discard": False,
                "minimum_limit": 0,
                "maximum_limit": 0,
            }
        precount = ShelfObject.objects.filter(shelf=13).count()
        url = reverse("laboratory:api-shelfobject-create-shelfobject",
                      kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, content_type='application/json')
        poscount = ShelfObject.objects.filter(shelf=13).count()
        self.assertEqual(response.status_code,201)
        self.assertTrue(json.loads(response.content)['detail'], _("The creation was performed successfully."))
        self.assertTrue(poscount>precount)
        obs=ShelfObjectObservation.objects.last()
        self.assertTrue(obs.description==data['course_name'])

    def test_create_shelfobject_equipment(self):
        """
        Test for API create_shelfobject when the objecttype is 2 and all the data is given correctly
        Example objecttype represents: 0)Reactive. 1)Material. 2)Equipment
        """

        data = {
                "shelf": 13,
                "object": 2,
                "objecttype": 1,
                "status": 1,
                "quantity": 23.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": 1,
                "measurement_unit": 59,
                "marked_as_discard": False,
                "minimum_limit": 0,
                "course_name": "A reactive product",
                "maximum_limit": 0,
            }
        precount=ShelfObject.objects.filter(shelf=13).count()
        url = reverse("laboratory:api-shelfobject-create-shelfobject",  kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, content_type='application/json')
        poscount=ShelfObject.objects.filter(shelf=13).count()
        self.assertEqual(response.status_code,201)
        self.assertTrue(json.loads(response.content)['detail'], _("The creation was performed successfully."))
        self.assertTrue(poscount>precount)
        obs=ShelfObjectObservation.objects.last()
        self.assertTrue(obs.description==data['course_name'])

    def test_create_shelfobject_reactive(self):
        """
        Test for API create_shelfobject when the objecttype is 0 and all the data is given correctly
        Example objecttype represents: 0)Reactive. 1)Material. 2)Equipment
        """

        self.material.type=1
        self.material.save()
        data = {
                "shelf": 13,
                "object": 2,
                "batch": 2,
                "objecttype": 0,
                "status": 1,
                "quantity": 23.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": 1,
                "course_name": "A reactive product",
                "measurement_unit": 59,
                "marked_as_discard": False,
                "minimum_limit": 0,
                "maximum_limit": 0,
                "container": self.material.pk
            }
        precount=ShelfObject.objects.filter(shelf=13).count()
        url = reverse("laboratory:api-shelfobject-create-shelfobject",  kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, content_type='application/json')
        poscount=ShelfObject.objects.filter(shelf=13).count()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(json.loads(response.content)['detail'], _("The creation was performed successfully."))
        self.assertTrue(poscount>precount)
        obs=ShelfObjectObservation.objects.last()
        self.assertTrue(obs.description==data['course_name'])

    def test_create_shelfobject_reactive_not_container(self):
        """
        Test for API create_shelfobject when the objecttype is a reactive and the container or recipient is null
        """
        data = {
                "shelf": 13,
                "object": 2,
                "batch": 2,
                "objecttype": 0,
                "status": 1,
                "quantity": 23.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": 1,
                "course_name": "A reactive product",
                "measurement_unit": 59,
                "marked_as_discard": False,
                "minimum_limit": 0,
                "maximum_limit": 0,
            }
        precount=ShelfObject.objects.filter(shelf=13).count()
        url = reverse("laboratory:api-shelfobject-create-shelfobject",  kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, content_type='application/json')
        poscount=ShelfObject.objects.filter(shelf=13).count()
        self.assertTrue(json.loads(response.content)['errors']['container'][0], _("This field is required."))
        self.assertTrue(poscount==precount)
        self.assertEqual(response.status_code,400)

    def test_create_shelfobject_shelf_limit(self):
        """
        Test for API create_shelfobject when the shelfobject quantity is greater than shelf quantity
        for example: shelfobject quantity is 80 and the shelf quantity limit is 40
        """
        self.material.type = 1
        self.material.save()
        data = {
                "shelf": 13,
                "object": 2,
                "batch": 2,
                "objecttype": 0,
                "status": 1,
                "quantity": 80.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": 1,
                "measurement_unit": 59,
                "marked_as_discard": False,
                "minimum_limit": 0,
                "maximum_limit": 0,
                "container": self.material.pk
        }
        precount = ShelfObject.objects.filter(shelf=13).count()
        url = reverse("laboratory:api-shelfobject-create-shelfobject",
                          kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, content_type='application/json')
        poscount = ShelfObject.objects.filter(shelf=13).count()
        self.assertEqual(response.status_code, 400)
        self.assertTrue(json.loads(response.content)['errors']['quantity'], _("Quantity can\'t greater than shelf quantity limit 40.0"))
        self.assertTrue(poscount == precount)

    def test_create_shelfobject_shelf_quantity_measurement_unit(self):
        """
        Test for API create_shelfobject when the shelfobject quantity is greater than shelf quantity
        and their measurement_unit is different
        """
        self.material.type = 1
        self.material.save()
        data = {
                "shelf": 13,
                "object": 2,
                "batch": 2,
                "objecttype": 0,
                "status": 1,
                "quantity": 80.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": 1,
                "measurement_unit": 60,
                "marked_as_discard": False,
                "course_name": "A reactive product",
                "minimum_limit": 0,
                "maximum_limit": 0,
                "container": self.material.pk
        }
        precount = ShelfObject.objects.filter(shelf=13).count()
        url = reverse("laboratory:api-shelfobject-create-shelfobject",
                          kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, content_type='application/json')
        poscount = ShelfObject.objects.filter(shelf=13).count()
        self.assertEqual(response.status_code, 400)
        self.assertTrue(poscount == precount)
        self.assertTrue(json.loads(response.content)['errors']['measurement_unit'][0]=="Measurement unit can\'t different than shelf measurement unit")
        self.assertTrue(json.loads(response.content)['errors']['quantity'][0], _("Quantity can\'t greater than shelf quantity limit 40.0"))

    def test_create_shelfobject_limits_errors(self):
        """
        Test for API create_shelfobject when the shelfobject minimum limit is greater than shelfobject maximum limit
        """
        self.material.type = 1
        self.material.save()
        data = {
                "shelf": 13,
                "object": 2,
                "batch": 2,
                "objecttype": 0,
                "status": 1,
                "quantity": 40.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": 1,
                "measurement_unit": 59,
                "marked_as_discard": False,
                "minimum_limit": 39,
                "maximum_limit": 5,
                "container": self.material.pk
        }
        precount = ShelfObject.objects.filter(shelf=13).count()
        url = reverse("laboratory:api-shelfobject-create-shelfobject",
                          kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, content_type='application/json')
        poscount = ShelfObject.objects.filter(shelf=13).count()
        self.assertEqual(response.status_code, 400)
        self.assertTrue(json.loads(response.content)['non_field_errors'], _("Minimum limit can't be greater than maximum limit"))
        self.assertTrue(poscount == precount)

    def test_create_shelfobject_other_lab(self):
        self.material.type = 1
        self.client.logout()
        self.client.force_login(self.user)
        org = OrganizationStructure.objects.get(pk=2)
        lab = Laboratory.objects.create(name="Lab x", organization=org)
        data = {
                "shelf": 13,
                "object": 2,
                "batch": 2,
                "objecttype": 1,
                "status": 1,
                "quantity": 40.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": lab.pk,
                "measurement_unit": 59,
                "marked_as_discard": False,
                "minimum_limit": 0,
                "maximum_limit": 5,
                "container": self.material.pk
        }

        precount = ShelfObject.objects.filter(shelf=13).count()
        url = reverse("laboratory:api-shelfobject-create-shelfobject",
                          kwargs={"org_pk": self.org_pk, "lab_pk": lab.pk})
        response = self.client.post(url, data=data, content_type='application/json')
        poscount = ShelfObject.objects.filter(shelf=13).count()
        self.assertEqual(response.status_code, 403)
        self.assertTrue(json.loads(response.content)['detail'] == _('You do not have permission to perform this action.'))
        self.assertTrue(poscount == precount)

    def test_create_shelfobject_other_organization(self):
        self.material.type = 1
        self.client.logout()
        self.client.force_login(self.user)
        data = {
                "shelf": 13,
                "object": 2,
                "batch": 2,
                "objecttype": 1,
                "status": 1,
                "quantity": 40.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": self.lab.pk,
                "measurement_unit": 59,
                "marked_as_discard": False,
                "minimum_limit": 0,
                "maximum_limit": 5,
                "container": self.material.pk
        }

        precount = ShelfObject.objects.filter(shelf=13).count()
        url = reverse("laboratory:api-shelfobject-create-shelfobject",
                          kwargs={"org_pk": 4, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, content_type='application/json')
        poscount = ShelfObject.objects.filter(shelf=13).count()
        self.assertEqual(response.status_code, 403)
        self.assertTrue(json.loads(response.content)['detail'] == _('You do not have permission to perform this action.'))
        self.assertTrue(poscount == precount)


    def test_create_shelfobject_shelf_unlimit(self):
        """
        Test for API create_shelfobject when the shelf quantity is infinity
        """
        shelf = Shelf.objects.get(pk=13)
        shelf.infinity_quantity=True
        shelf.save()
        self.material.type = 1
        self.client.logout()
        self.client.force_login(self.user)
        data = {
                "shelf": 13,
                "object": 2,
                "batch": 2,
                "objecttype": 1,
                "status": 1,
                "quantity": 90000.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": self.lab.pk,
                "measurement_unit": 59,
                "marked_as_discard": False,
                "minimum_limit": 0,
                "maximum_limit": 5,
                "container": self.material.pk
        }

        precount = ShelfObject.objects.filter(shelf=13).count()
        url = reverse("laboratory:api-shelfobject-create-shelfobject",
                          kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, content_type='application/json')
        poscount = ShelfObject.objects.filter(shelf=13).count()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(json.loads(response.content)['detail'] == _('The creation was performed successfully.'))
        self.assertTrue(poscount > precount)

    def test_create_shelfobject_shelf_unlimit_unit_error(self):
        """
        Test for API create_shelfobject when the shelf quantity is infinity and have a measurement unit,
        but the shelfobject the measurement unit is distint than the shelf
        """
        shelf = Shelf.objects.get(pk=13)
        shelf.infinity_quantity=True
        shelf.save()
        self.material.type = 1
        self.client.logout()
        self.client.force_login(self.user)
        data = {
                "shelf": 13,
                "object": 2,
                "batch": 2,
                "objecttype": 1,
                "status": 1,
                "quantity": 90000.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": self.lab.pk,
                "measurement_unit": 60,
                "marked_as_discard": False,
                "minimum_limit": 0,
                "maximum_limit": 5,
                "container": self.material.pk
        }

        precount = ShelfObject.objects.filter(shelf=13).count()
        url = reverse("laboratory:api-shelfobject-create-shelfobject",
                          kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, content_type='application/json')
        poscount = ShelfObject.objects.filter(shelf=13).count()
        self.assertEqual(response.status_code, 400)
        self.assertTrue(json.loads(response.content)['errors']['measurement_unit'][0] == _("Measurement unit can't different than shelf measurement unit"))
        self.assertTrue(poscount == precount)

    def test_create_shelfobject_shelf_unlimit_units(self):
        """
        Test for API create_shelfobject when the shelf quantity is infinity and don't have measurement unit,
        """
        shelf = Shelf.objects.get(pk=13)
        shelf.infinity_quantity=True
        shelf.measurement_unit=None
        shelf.save()
        self.material.type = 1
        self.client.logout()
        self.client.force_login(self.user)
        data = {
                "shelf": 13,
                "object": 2,
                "batch": 2,
                "objecttype": 1,
                "status": 1,
                "quantity": 90000.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": self.lab.pk,
                "measurement_unit": 60,
                "marked_as_discard": False,
                "minimum_limit": 0,
                "maximum_limit": 5,
                "container": self.material.pk
        }

        precount = ShelfObject.objects.filter(shelf=13).count()
        url = reverse("laboratory:api-shelfobject-create-shelfobject",
                          kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, content_type='application/json')
        poscount = ShelfObject.objects.filter(shelf=13).count()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(json.loads(response.content)['detail'] == _('The creation was performed successfully.'))
        self.assertTrue(poscount > precount)

    def test_create_discard_shelfobject(self):
        """
        Test for API create_shelfobject when the shelf is a discard
        """
        shelf = Shelf.objects.get(pk=13)
        shelf.discard=True
        shelf.save()
        data = {
                "shelf": 13,
                "object": 1,
                "objecttype": 1,
                "status": 1,
                "quantity": 23.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": 1,
                "measurement_unit": 59,
                "course_name": "A reactive product",
                "marked_as_discard": True,
                "minimum_limit": 0,
                "maximum_limit": 0,
            }
        precount = ShelfObject.objects.filter(shelf=13).count()
        url = reverse("laboratory:api-shelfobject-create-shelfobject",
                      kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, content_type='application/json')
        poscount = ShelfObject.objects.filter(shelf=13).count()
        self.assertEqual(response.status_code,201)
        self.assertTrue(json.loads(response.content)['detail'], _("The creation was performed successfully."))
        self.assertTrue(poscount>precount)
        obs=ShelfObjectObservation.objects.last()
        self.assertTrue(obs.description==data['course_name'])

    def test_create_discard_shelfobject_units_error(self):
        """
        Test for API create_shelfobject when the shelf is a discard and have a measurement unit,
        but the shelfobject the measurement unit is distint than the shelf
        """
        shelf = Shelf.objects.get(pk=13)
        shelf.discard=True
        shelf.save()
        data = {
                "shelf": 13,
                "object": 1,
                "objecttype": 1,
                "status": 1,
                "quantity": 23.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": 1,
                "measurement_unit": None,
                "course_name": "A reactive product",
                "marked_as_discard": True,
                "minimum_limit": 0,
                "maximum_limit": 0,
            }
        precount = ShelfObject.objects.filter(shelf=13).count()
        url = reverse("laboratory:api-shelfobject-create-shelfobject",
                      kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, content_type='application/json')
        poscount = ShelfObject.objects.filter(shelf=13).count()
        self.assertEqual(response.status_code,400)
        self.assertTrue(json.loads(response.content)['errors']['measurement_unit'][0], _("This field may not be null."))
        self.assertTrue(poscount==precount)

    def test_create_discard_shelfobject_quantity_error(self):
        """
        Test for API create_shelfobject when the shelfobject quantity is greater than shelf quantity
        """
        shelf = Shelf.objects.get(pk=13)
        shelf.discard=True
        shelf.save()
        data = {
                "shelf": 13,
                "object": 1,
                "objecttype": 1,
                "status": 1,
                "quantity": 90.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": 1,
                "measurement_unit": 59,
                "course_name": "A reactive product",
                "marked_as_discard": True,
                "minimum_limit": 0,
                "maximum_limit": 0,
            }
        precount = ShelfObject.objects.filter(shelf=13).count()
        url = reverse("laboratory:api-shelfobject-create-shelfobject",
                      kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, content_type='application/json')
        poscount = ShelfObject.objects.filter(shelf=13).count()
        self.assertEqual(response.status_code,400)
        self.assertTrue(json.loads(response.content)['errors']['quantity'][0], _("Quantity can\'t greater than shelf quantity limit 40.0"))
        self.assertTrue(poscount==precount)

    def test_create_shelfobject_user_forbidden(self):
        self.client.logout()
        data = {
                "shelf": 13,
                "object": 1,
                "objecttype": 1,
                "status": 1,
                "quantity": 90.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": 1,
                "measurement_unit": 59,
                "course_name": "A reactive product",
                "minimum_limit": 0,
                "maximum_limit": 0,
            }
        precount = ShelfObject.objects.filter(shelf=13).count()
        url = reverse("laboratory:api-shelfobject-create-shelfobject",
                      kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, content_type='application/json')
        poscount = ShelfObject.objects.filter(shelf=13).count()
        self.assertEqual(response.status_code, 403)
        self.assertTrue(precount == poscount)
        self.assertTrue(json.loads(response.content)['detail'] == _("Authentication credentials were not provided."))

    def test_create_shelfobject_no_objecttype(self):
        """
        Test for API create_shelfobject when don't have objecttype
        """
        data = {
                "shelf": 13,
                "object": 1,
                "status": 1,
                "quantity": 23.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": 1,
                "measurement_unit": 59,
                "course_name": "A reactive product",
                "marked_as_discard": False,
                "minimum_limit": 0,
                "maximum_limit": 0,
            }
        precount = ShelfObject.objects.filter(shelf=13).count()
        url = reverse("laboratory:api-shelfobject-create-shelfobject",
                      kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, content_type='application/json')
        poscount = ShelfObject.objects.filter(shelf=13).count()
        self.assertEqual(response.status_code,400)

        self.assertTrue(json.loads(response.content)['objecttype'][0], _("This field is required."))
        self.assertTrue(poscount==precount)

    def test_create_shelfobject_object_no_available_in_shelf(self):
        """
        Test for API create_shelfobject when the shelf limit_only_object is True and the object is receiving
        not is available for that shelf
        """
        shelf=Shelf.objects.get(pk=13)
        shelf.limit_only_objects=True
        obj=Object.objects.get(pk=2)
        shelf.available_objects_when_limit.add(obj)
        shelf.save()
        data = {
                "shelf": 13,
                "object": 1,
                "status": 1,
                "objecttype": 1,
                "quantity": 23.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": 1,
                "measurement_unit": 59,
                "course_name": "A reactive product",
                "marked_as_discard": False,
                "minimum_limit": 0,
                "maximum_limit": 0,
            }
        precount = ShelfObject.objects.filter(shelf=13).count()
        url = reverse("laboratory:api-shelfobject-create-shelfobject",
                      kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, content_type='application/json')
        poscount = ShelfObject.objects.filter(shelf=13).count()
        self.assertEqual(response.status_code,400)
        self.assertTrue(json.loads(response.content)["errors"]['object'][0]==_("Object is not available in these shelf"))
        self.assertTrue(poscount==precount)

    def test_create_shelfobject_object_available_in_shelf(self):
        """
        Test for API create_shelfobject when the shelf limit_only_object is True and the object is receiving
        is available for that shelf
        """
        shelf=Shelf.objects.get(pk=13)
        shelf.limit_only_objects=True
        obj=Object.objects.get(pk=1)
        shelf.available_objects_when_limit.add(obj)
        shelf.save()
        data = {
                "shelf": 13,
                "object": 1,
                "status": 1,
                "objecttype": 1,
                "quantity": 23.0,
                "limit_quantity": 7.0,
                "in_where_laboratory": 1,
                "measurement_unit": 59,
                "course_name": "A reactive product",
                "marked_as_discard": False,
                "minimum_limit": 0,
                "maximum_limit": 0,
            }
        precount = ShelfObject.objects.filter(shelf=13).count()
        url = reverse("laboratory:api-shelfobject-create-shelfobject",
                      kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, content_type='application/json')
        poscount = ShelfObject.objects.filter(shelf=13).count()
        self.assertEqual(response.status_code,201)
        self.assertTrue(poscount>precount)
