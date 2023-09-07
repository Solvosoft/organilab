from laboratory.models import Laboratory,Catalog, OrganizationStructure
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
import json
from laboratory.tests.utils import BaseShelfobjectStatusSetUpTest

class ShelfObjectStatusTest(BaseShelfobjectStatusSetUpTest):

    def test_create_status(self):
        """
        Test for API create_status when all the data is given correctly
        """
        url = reverse("laboratory:api-shelfobject-create-status", kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data={'description': 'Buen Estado'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Catalog.objects.filter(key="shelfobject_status").count() == 2)
        self.assertContains(response=response, text=_('The item was created successfully'))

    def test_create_not_permission(self):
        """
        Test for API create_status when user dont have permissions to creates status
        """
        self.client.logout()
        self.client.force_login(self.user1)
        url = reverse("laboratory:api-shelfobject-create-status", kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data={'description': 'Buen Estado'})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Catalog.objects.filter(key="shelfobject_status").count() == 1)
        self.assertTrue(
            json.loads(response.content)['detail'] == _('You do not have permission to perform this action.'))

    def test_create_status_not_laboratory(self):
        """
        Test for API create_status when the lab_pk doesn't belong to laboratory is associated
        """
        self.client.logout()
        self.client.force_login(self.user)
        org = OrganizationStructure.objects.get(pk=2)
        aa = Laboratory.objects.create(name="Lab x", organization=org)
        url = reverse("laboratory:api-shelfobject-create-status", kwargs={"org_pk": self.org_pk, "lab_pk": aa.pk})
        response = self.client.post(url, data={'description': 'Buen Estado'})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Catalog.objects.filter(key="shelfobject_status").count() == 1)
        self.assertTrue(
            json.loads(response.content)['detail'] == _('You do not have permission to perform this action.'))

    def test_create_status_not_organization(self):
        """
         Test for API create_status when the org_pk doesn't belong to an organization the user is associated
         """
        self.client.logout()
        self.client.force_login(self.user)

        url = reverse("laboratory:api-shelfobject-create-status", kwargs={"org_pk": 3, "lab_pk": self.lab.pk})
        response = self.client.post(url, data={'description': 'Buen Estado'})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Catalog.objects.filter(key="shelfobject_status").count() == 1)
        self.assertTrue(
            json.loads(response.content)['detail'] == _('You do not have permission to perform this action.'))

    def test_create_status_empty_description(self):
        """
         Test for API create_status when the description is empty in the request
        """
        self.client.logout()
        self.client.force_login(self.user)

        url = reverse("laboratory:api-shelfobject-create-status", kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data={'description': ''})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Catalog.objects.filter(key="shelfobject_status").count() == 1)
        self.assertTrue(json.loads(response.content)['errors']['description'][0] == _('This field may not be blank.'))

