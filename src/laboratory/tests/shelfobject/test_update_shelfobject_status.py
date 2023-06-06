from laboratory.models import Laboratory, ShelfObjectObservation, ShelfObject, Catalog, \
    OrganizationStructure
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
import json
from laboratory.tests.utils import BaseShelfobjectStatusSetUpTest

class ShelfObjectStatusTest(BaseShelfobjectStatusSetUpTest):
    def test_update_status(self):
        """
        Test for API update_status when all the data is given correctly
        """
        self.client.logout()
        self.client.force_login(self.user)
        catalog = Catalog.objects.create(key="shelfobject_status", description="Buen estado")
        data = {
            "shelfobject": 4,
            "status": catalog.pk,
            "description": "Change Status"
        }
        url = reverse("laboratory:api-shelfobject-update-status",
                      kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk, "pk": 4})
        response = self.client.put(url, data=data, content_type='application/json')
        shelfobject = ShelfObject.objects.get(pk=4)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(shelfobject.status.pk == data['status'])

        self.assertContains(response=response, text="Buen estado")
        self.assertTrue(json.loads(response.content)['detail'] == _("The object status was updated successfully"))
        observation_created = ShelfObjectObservation.objects.last()
        self.assertTrue(observation_created.description == data['description'])
        self.assertContains(response=response, text=catalog.description)

    def test_update_status_not_permission(self):
        """
        Test for API update_status when user dont have permissions to creates status
        """
        self.client.logout()
        self.client.force_login(self.user1)
        catalog = Catalog.objects.create(key="shelfobject_status", description="Buen estado")
        shelfobject = ShelfObject.objects.get(pk=4)

        data = {
            "shelfobject": 4,
            "status": catalog.pk,
            "description": "Change Status"
        }
        url = reverse("laboratory:api-shelfobject-update-status",
                      kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk, "pk": 4})
        response = self.client.put(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(shelfobject.status == None)
        self.assertTrue(
            json.loads(response.content)['detail'] == _('You do not have permission to perform this action.'))

    def test_update_status_user_forbidden(self):
        """
        Test for API update_status when user without login try to update a shelgobject status
        """
        self.client.logout()
        catalog = Catalog.objects.create(key="shelfobject_status", description="Buen estado")
        shelfobject = ShelfObject.objects.get(pk=4)

        data = {
            "shelfobject": 4,
            "status": catalog.pk,
            "description": "Change Status"
        }
        url = reverse("laboratory:api-shelfobject-update-status",
                      kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk, "pk": 4})
        response = self.client.put(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(shelfobject.status == None)
        self.assertTrue(json.loads(response.content)['detail'] == _("Authentication credentials were not provided."))

    def test_update_status_form_error(self):
        """
        Test for API update_status when don't have status field in the request
        """
        shelfobject = ShelfObject.objects.get(pk=4)

        data = {
            "shelfobject": 4,
            "description": "Change Status"
        }
        url = reverse("laboratory:api-shelfobject-update-status",
                      kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk, "pk": 4})
        response = self.client.put(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(shelfobject.status == None)
        self.assertTrue(json.loads(response.content)['errors']['status'][0] == _("This field is required."))

    def test_update_status_error(self):
        """
        Test for API update_status when the status doesn't belong to shelfobject_status catalog
        """
        shelfobject = ShelfObject.objects.get(pk=4)
        data = {
            "shelfobject": 4,
            "status": 157,
            "description": "Change Status"
        }
        url = reverse("laboratory:api-shelfobject-update-status",
                      kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk, "pk": 4})
        response = self.client.put(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(shelfobject.status == None)

    def test_update_status_not_laboratory(self):
        """
        Test for API update_status when the lab_pk doesn't belong to laboratory is associated
        """
        self.client.logout()
        self.client.force_login(self.user)
        org = OrganizationStructure.objects.get(pk=2)
        aa = Laboratory.objects.create(name="Lab x", organization=org)
        data = {
            "shelfobject": 4,
            "status":1,
            "description": "Change Status"
        }
        url = reverse("laboratory:api-shelfobject-update-status",
                      kwargs={"org_pk": self.org_pk, "lab_pk": aa.pk, "pk": 4})
        response = self.client.put(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Catalog.objects.filter(key="shelfobject_status").count() == 1)
        self.assertTrue(
            json.loads(response.content)['detail'] == _('You do not have permission to perform this action.'))

    def test_update_status_not_organization(self):
        """
         Test for API update_status when the org_pk doesn't belong to an organization the user is associated
        """
        org = OrganizationStructure.objects.get(pk=2)
        data = {
            "shelfobject": 4,
            "status":1,
            "description": "Change Status"
        }
        url = reverse("laboratory:api-shelfobject-update-status",
                      kwargs={"org_pk": org.pk, "lab_pk": self.lab.pk, "pk": 4})
        response = self.client.put(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Catalog.objects.filter(key="shelfobject_status").count() == 1)
        self.assertTrue(
            json.loads(response.content)['detail'] == _('You do not have permission to perform this action.'))

    def test_update_status_empty_description(self):
        """
        Test for API create_status when the description of the reason is empty in the request
        """
        catalog = Catalog.objects.create(key="shelfobject_status", description="Buen estado")

        data = {
            "shelfobject": 4,
            "status": catalog.pk,
            "description": ""
        }
        url = reverse("laboratory:api-shelfobject-update-status",
                      kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk, "pk": 4})
        response = self.client.put(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Catalog.objects.filter(key="shelfobject_status").count() == 2)
        self.assertTrue(json.loads(response.content)['errors']['description'][0] == _('This field may not be blank.'))

    def test_update_status_shelfobject_other_lab(self):
        """
        Test for API update_status when the shelfobject laborotory don't belong to the laboratory is login
        """
        catalog = Catalog.objects.create(key="shelfobject_status", description="Buen estado")
        shelfobject= ShelfObject.objects.get(pk=4)
        org = OrganizationStructure.objects.get(pk=2)
        lab = Laboratory.objects.create(name="Lab x", organization=org)
        shelfobject.in_where_laboratory=lab
        shelfobject.save()
        data = {
            "shelfobject": shelfobject.pk,
            "status": catalog.pk,
            "description": "Ok"
        }
        url = reverse("laboratory:api-shelfobject-update-status",
                      kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk, "pk": 4})
        response = self.client.put(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Catalog.objects.filter(key="shelfobject_status").count() == 2)
        self.assertTrue(json.loads(response.content)['errors']['shelf_object'][0]=="Object does not exist in the laboratory.")
