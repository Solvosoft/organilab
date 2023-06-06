from django.urls import reverse
from .test_shelfobject_api import ShelfObjectAPITest


class ShelfObjectListCommentsTest(ShelfObjectAPITest):

    def test_shelfobject_api_list_comments(self):
        """
        Test for API list_comments when all the data is given correctly
        """
        response = self.client.get(reverse('laboratory:api-shelfobject-list-comments',
                                           kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response=response, text="Test observation 1")
        self.assertContains(response=response, text="Test observation 2")

    def test_shelfobject_api_list_comments_without_creator(self):
        """
        Test for API list_comments when the shelf object doesn't have a creator
        """
        response = self.client.get(reverse('laboratory:api-shelfobject-list-comments',
                                           kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 2}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response=response, text="Test observation 3")

    def test_shelfobject_api_list_comments_not_found(self):
        """
        Test for API list_comments shelf object not found
        pk = 115, Shelf Object that doesn't exist in the DB
        """
        response = self.client.get(reverse('laboratory:api-shelfobject-list-comments',
                                           kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 115}))
        self.assertEqual(response.status_code, 404)

    def test_shelfobject_api_list_comments_shelfobject_not_in_laboratory(self):
        """
        Test for API list_comments when shelf object doesn't belong to laboratory
        lab_pk = 3, PK that exists in the DB but doesn't contain the pk given
        pk = Shelf Object that belongs to lab_pk = 1
        """
        response = self.client.get(reverse('laboratory:api-shelfobject-list-comments', kwargs={'org_pk': self.org_pk, 'lab_pk': 3, 'pk': 1}))
        self.assertEqual(response.status_code, 404)

    def test_shelfobject_api_list_comments_user_with_permissions_forbidden(self):
        """
        Test for API list_comments when user have permissions in their organization
        but don't have access to the specified laboratory/organization
        """
        self.client.logout()
        self.client.force_login(self.user2)
        response = self.client.get(reverse('laboratory:api-shelfobject-list-comments',
                                           kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}))
        self.assertEqual(response.status_code, 403)

    def test_shelfobject_api_list_comments_user_without_permissions_forbidden(self):
        """
        Test for API list_comments when user don't have any permissions and
        don't have access to the specified laboratory/organization
        """
        self.client.logout()
        self.client.force_login(self.user3)
        response = self.client.get(reverse('laboratory:api-shelfobject-list-comments',
                                           kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}))
        self.assertEqual(response.status_code, 403)

    def test_shelfobject_api_list_comments_anonymous_user_forbidden(self):
        """
        Test for API list_comments when anonymous user tries to access
        """
        self.client.logout()
        response = self.client.get(reverse('laboratory:api-shelfobject-list-comments',
                                           kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}))
        self.assertEqual(response.status_code, 403)