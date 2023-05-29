import datetime
from laboratory.models import Laboratory
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class ShelfObjectAPITest(TestCase):
    fixtures = ["laboratory_data.json"]
    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.user2 = User.objects.get(pk=2)
        self.org_pk = 1
        self.lab = Laboratory.objects.first()
        self.client.force_login(self.user)

    """
    Test for API details
    """
    def test_shelfobject_api_details(self):
        response = self.client.get(reverse('laboratory:api-shelfobject-details', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 2}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response=response, text="Cal 100 gr")
        self.assertContains(response=response, text="CA777")
        self.assertContains(response=response, text="Reactivo")
        self.assertContains(response=response, text="security_sheets/test_characteristics.pdf")
        self.assertContains(response=response, text="CHO")

    """
    Test for API details shelf object not found
    """
    def test_shelfobject_api_details_not_found(self):
        response = self.client.get(reverse('laboratory:api-shelfobject-details', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 5}))
        self.assertEqual(response.status_code, 404)

    """
    Test for API details when shelf object doesn't belong to laboratory
    """
    def test_shelfobject_api_details_shelfobject_not_in_laboratory(self):
        response = self.client.get(reverse('laboratory:api-shelfobject-details', kwargs={'org_pk': self.org_pk, 'lab_pk': 3, 'pk': 1}))
        self.assertEqual(response.status_code, 404)

    """
    Test for API details when user don't have access to laboratory/organization
    """
    def test_shelfobject_api_details_forbidden(self):
        self.client.logout()
        self.client.force_login(self.user2)
        response = self.client.get(reverse('laboratory:api-shelfobject-details', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}))
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        self.client.force_login(self.user)

    """
    Test for API list_comments
    """
    def test_shelfobject_api_list_comments(self):
        response = self.client.get(reverse('laboratory:api-shelfobject-list-comments',
                                           kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response=response, text="Test observation 1")
        self.assertContains(response=response, text="Test observation 2")

    """
    Test for API list_comments shelf object not found
    """
    def test_shelfobject_api_list_comments_not_found(self):
        response = self.client.get(reverse('laboratory:api-shelfobject-list-comments',
                                           kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 5}))
        self.assertEqual(response.status_code, 404)

    """
    Test for API list_comments when shelf object doesn't belong to laboratory
    """
    def test_shelfobject_api_list_comments_shelfobject_not_in_laboratory(self):
        response = self.client.get(reverse('laboratory:api-shelfobject-list-comments', kwargs={'org_pk': self.org_pk, 'lab_pk': 3, 'pk': 1}))
        self.assertEqual(response.status_code, 404)

    """
    Test for API list_comments when user don't have access to laboratory/organization
    """
    def test_shelfobject_api_list_comments_forbidden(self):
        self.client.logout()
        self.client.force_login(self.user2)
        response = self.client.get(reverse('laboratory:api-shelfobject-list-comments',
                                           kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}))
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        self.client.force_login(self.user)

    """
    Test for API create_comments
    """
    def test_shelfobject_api_create_comments(self):
        data = {'action_taken': 'Object Change', 'description': 'Test Comment for testing', 'prefix': ''}
        response = self.client.post(reverse('laboratory:api-shelfobject-create-comments',
                                           kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}),
                                    data=data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)

    """
    Test for API create_comments shelf object not found
    """
    def test_shelfobject_api_create_comments_not_found(self):
        data = {'action_taken': 'Object Change', 'description': 'Test Comment for testing', 'prefix': ''}
        response = self.client.post(reverse('laboratory:api-shelfobject-create-comments',
                                            kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 5}),
                                    data=data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 404)

    """
    Test for API create_comments when shelf object doesn't belong to laboratory
    """
    def test_shelfobject_api_create_comments_shelfobject_not_in_laboratory(self):
        data = {'action_taken': 'Object Change', 'description': 'Test Comment for testing', 'prefix': ''}
        response = self.client.post(reverse('laboratory:api-shelfobject-create-comments',
                                            kwargs={'org_pk': self.org_pk, 'lab_pk': 3, 'pk': 1}),
                                    data=data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 404)

    """
    Test for API create_comments when user don't have access to laboratory/organization
    """
    def test_shelfobject_api_create_comments_forbidden(self):
        self.client.logout()
        self.client.force_login(self.user2)
        data = {'action_taken': 'Object Change', 'description': 'Test Comment for testing', 'prefix': ''}
        response = self.client.post(reverse('laboratory:api-shelfobject-create-comments',
                                            kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}),
                                    data=data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        self.client.force_login(self.user)

    """
    Test for API delete
    """
    def test_shelfobject_api_delete(self):
        delete_url = reverse('laboratory:api-shelfobject-delete', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id})
        response = self.client.delete(delete_url, data={'shelfobj': 1}, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    """
    Test for API delete shelf object not found
    """
    def test_shelfobject_api_delete_not_found(self):
        delete_url = reverse('laboratory:api-shelfobject-delete', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id})
        response = self.client.delete(delete_url, data={'shelfobj': 5}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    """
    Test for API delete when shelf object doesn't belong to laboratory
    """
    def test_shelfobject_api_delete_shelfobject_not_in_laboratory(self):
        delete_url = reverse('laboratory:api-shelfobject-delete', kwargs={'org_pk': self.org_pk, 'lab_pk': 3})
        response = self.client.delete(delete_url, data={'shelfobj': 2}, content_type='application/json')
        self.assertContains(response=response, text=_("Object does not exist in the laboratory."), status_code=400)

    """
    Test for API delete when user don't have access to laboratory/organization
    """
    def test_shelfobject_api_delete_forbidden(self):
        delete_url = reverse('laboratory:api-shelfobject-delete', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id})
        self.client.logout()
        self.client.force_login(self.user2)
        response = self.client.delete(delete_url, data={'shelfobj': 1}, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        self.client.force_login(self.user)




