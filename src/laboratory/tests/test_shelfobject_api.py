from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from auth_and_perms.models import Rol, ProfilePermission
from laboratory.models import Laboratory, ShelfObjectObservation, ShelfObject
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.utils.translation import gettext_lazy as _


class ShelfObjectAPITest(TestCase):
    fixtures = ["laboratory_data.json"]
    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.user2 = User.objects.get(pk=2)
        self.user3 = User.objects.get(pk=3)
        self.org_pk = 1
        self.lab = Laboratory.objects.first()
        self.client.force_login(self.user)
        user2_role = Rol.objects.create(name="Test Role for User 2", color="#FFF")
        permission = Permission.objects.filter(codename__contains="shelfobject")
        user2_role.permissions.add(*permission)
        profile_permission = ProfilePermission.objects.create(profile=self.user2.profile,
                                                              object_id=2,
                                                              content_type=ContentType.objects.get(app_label='laboratory',
                                                                                                   model='organizationstructure')
                                                              )
        profile_permission.rol.add(user2_role)

    def test_shelfobject_api_details_with_substance_characteristics_and_features(self):
        """
        Test for API details success case with substance characteristics and features
        pk = 2 -> Shelf Object related to substance characteristics with pk = 1
        """
        response = self.client.get(reverse('laboratory:api-shelfobject-details', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 2}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response=response, text="Cal 100 gr")
        self.assertContains(response=response, text="CA777")
        self.assertContains(response=response, text="Reactivo")
        self.assertContains(response=response, text="security_sheets/test_characteristics.pdf")
        self.assertContains(response=response, text="CHO")

    def test_shelfobject_api_details_without_features(self):
        """
        Test for API details success case without features
        """
        response = self.client.get(reverse('laboratory:api-shelfobject-details', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response=response, text='"name": "Tanque 1000 mL"')
        self.assertNotContains(response=response, text='"object_features":null')

    def test_shelfobject_api_details_without_substance_characteristics(self):
        """
        Test for API details success case without substance characteristics
        Shelf Object with pk = 3 that doesn't have any features key
        """
        response = self.client.get(reverse('laboratory:api-shelfobject-details', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 3}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response=response, text='"name": "Cal 100 gr"')
        self.assertNotContains(response=response, text='"substance_characteristics":null')

    def test_shelfobject_api_details_shelf_object_only_with_required_fields(self):
        """
        Test for API details when an object with has no laboratory and only have required fields
        Shelf Object with pk = 4 that only have the required fields
        """
        response = self.client.get(reverse('laboratory:api-shelfobject-details',
                                           kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 4}))
        self.assertEqual(response.status_code, 404)
        pass

    def test_shelfobject_api_details_not_found(self):
        """
        Test for API details shelf object not found
        pk = 5, Shelf Object that doesn't exist in the DB
        """
        response = self.client.get(reverse('laboratory:api-shelfobject-details', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 5}))
        self.assertEqual(response.status_code, 404)

    def test_shelfobject_api_details_shelfobject_not_in_laboratory(self):
        """
        Test for API details when shelf object doesn't belong to laboratory
        lab_pk = 3, PK that exists in the DB but doesn't contain the pk given
        pk = Shelf Object that belongs to lab_pk = 1
        """
        response = self.client.get(reverse('laboratory:api-shelfobject-details', kwargs={'org_pk': self.org_pk, 'lab_pk': 3, 'pk': 1}))
        self.assertEqual(response.status_code, 404)

    def test_shelfobject_api_details_user_with_permissions_forbidden(self):
        """
        Test for API details when user have permissions in their organization
        but don't have access to the specified laboratory/organization
        """
        self.client.logout()
        self.client.force_login(self.user2)
        response = self.client.get(reverse('laboratory:api-shelfobject-details', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}))
        self.assertEqual(response.status_code, 403)

    def test_shelfobject_api_details_user_without_permissions_forbidden(self):
        """
        Test for API details when user don't have any permissions and
        don't have access to the specified laboratory/organization
        """
        self.client.logout()
        self.client.force_login(self.user3)
        response = self.client.get(reverse('laboratory:api-shelfobject-details', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}))
        self.assertEqual(response.status_code, 403)

    def test_shelfobject_api_details_anonymous_user_forbidden(self):
        """
        Test for API details when anonymous user tries to access
        """
        self.client.logout()
        response = self.client.get(reverse('laboratory:api-shelfobject-details', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}))
        self.assertEqual(response.status_code, 403)

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
        pk = 5, Shelf Object that doesn't exist in the DB
        """
        response = self.client.get(reverse('laboratory:api-shelfobject-list-comments',
                                           kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 5}))
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

    def test_shelfobject_api_create_comments(self):
        """
        Test for API create_comments when all the data is given correctly
        """
        data = {'action_taken': 'Object Change', 'description': 'Test Comment for testing', 'prefix': ''}
        response = self.client.post(reverse('laboratory:api-shelfobject-create-comments',
                                           kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}),
                                    data=data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        observation_created = ShelfObjectObservation.objects.last()
        self.assertEqual(ShelfObjectObservation.objects.filter(shelf_object=1).count(), 3)
        self.assertEqual(observation_created.description, 'Test Comment for testing')
        self.assertEqual(observation_created.action_taken, 'Object Change')
        log = LogEntry.objects.first()
        self.assertEqual(log.object_id, str(observation_created.id))
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action_flag, 1)

    def test_shelfobject_api_create_comments_wrong_content_type(self):
        """
        Test for API create_comments where the content_type isn't application/json
        content_type = 'application/octet-stream'
        """
        data = {'action_taken': 'Object Change', 'description': 'Test Comment for testing', 'prefix': ''}
        response = self.client.post(reverse('laboratory:api-shelfobject-create-comments',
                                           kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}),
                                    data=data,
                                    content_type='application/octet-stream')
        self.assertEqual(response.status_code, 415)

    def test_shelfobject_api_create_comments_no_description(self):
        """
        Test for API create_comments when description is None
        """
        data = {'action_taken': 'Object Change', 'description': '', 'prefix': ''}
        response = self.client.post(reverse('laboratory:api-shelfobject-create-comments',
                                           kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}),
                                    data=data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_shelfobject_api_create_comments_no_action_taken(self):
        """
        Test for API create_comments when action_taken is None
        """
        data = {'action_taken': '', 'description': 'Test Comment for testing', 'prefix': ''}
        response = self.client.post(reverse('laboratory:api-shelfobject-create-comments',
                                           kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}),
                                    data=data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_shelfobject_api_create_comments_not_found(self):
        """
       Test for API create_comments shelf object not found
        pk = 5, Shelf Object that doesn't exist in the DB
       """
        data = {'action_taken': 'Object Change', 'description': 'Test Comment for testing', 'prefix': ''}
        response = self.client.post(reverse('laboratory:api-shelfobject-create-comments',
                                            kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 5}),
                                    data=data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_shelfobject_api_create_comments_shelfobject_not_in_laboratory(self):
        """
        Test for API create_comments when shelf object doesn't belong to laboratory
        lab_pk = 3, PK that exists in the DB but doesn't contain the pk given
        pk = Shelf Object that belongs to lab_pk = 1
        """
        data = {'action_taken': 'Object Change', 'description': 'Test Comment for testing', 'prefix': ''}
        response = self.client.post(reverse('laboratory:api-shelfobject-create-comments',
                                            kwargs={'org_pk': self.org_pk, 'lab_pk': 3, 'pk': 1}),
                                    data=data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_shelfobject_api_create_comments_user_with_permissions_forbidden(self):
        """
        Test for API create_comments when user have permissions in their organization
        but don't have access to the specified laboratory/organization
        """
        self.client.logout()
        self.client.force_login(self.user2)
        data = {'action_taken': 'Object Change', 'description': 'Test Comment for testing', 'prefix': ''}
        response = self.client.post(reverse('laboratory:api-shelfobject-create-comments',
                                            kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}),
                                    data=data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_shelfobject_api_create_comments_user_without_permissions_forbidden(self):
        """
        Test for API create_comments when user don't have any permissions and
        don't have access to the specified laboratory/organization
        """
        self.client.logout()
        self.client.force_login(self.user3)
        data = {'action_taken': 'Object Change', 'description': 'Test Comment for testing', 'prefix': ''}
        response = self.client.post(reverse('laboratory:api-shelfobject-create-comments',
                                            kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}),
                                    data=data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_shelfobject_api_create_comments_anonymous_user_forbidden(self):
        """
        Test for API create_comments when anonymous user tries to access
        """
        self.client.logout()
        data = {'action_taken': 'Object Change', 'description': 'Test Comment for testing', 'prefix': ''}
        response = self.client.post(reverse('laboratory:api-shelfobject-create-comments',
                                            kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1}),
                                    data=data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.client.force_login(self.user)

    def test_shelfobject_api_delete(self):
        """
        Test for API delete success case, where the data is correctly given
        """
        delete_url = reverse('laboratory:api-shelfobject-delete', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id})
        response = self.client.delete(delete_url, data={'shelfobj': 1}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ShelfObjectObservation.objects.filter(shelf_object=1).count(), 0)
        log = LogEntry.objects.first()
        self.assertEqual(log.object_id, '1')
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action_flag, 3)


    def test_shelfobject_api_delete_not_found(self):
        """
        Test for API delete shelf object not found
        """
        delete_url = reverse('laboratory:api-shelfobject-delete', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id})
        response = self.client.delete(delete_url, data={'shelfobj': 5}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_shelfobject_api_delete_shelfobject_not_in_laboratory(self):
        """
        Test for API delete when shelf object doesn't belong to laboratory
        lab_pk = 3, PK that exists in the DB but doesn't contain the pk given
        pk = Shelf Object that belongs to lab_pk = 1
        """
        delete_url = reverse('laboratory:api-shelfobject-delete', kwargs={'org_pk': self.org_pk, 'lab_pk': 3})
        response = self.client.delete(delete_url, data={'shelfobj': 2}, content_type='application/json')
        self.assertContains(response=response, text=_("Object does not exist in the laboratory."), status_code=400)

    def test_shelfobject_api_delete_user_with_permissions_forbidden(self):
        """
        Test for API delete when user have permissions in their organization
        but don't have access to the specified laboratory/organization
        """
        delete_url = reverse('laboratory:api-shelfobject-delete', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id})
        self.client.logout()
        self.client.force_login(self.user2)
        response = self.client.delete(delete_url, data={'shelfobj': 1}, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_shelfobject_api_delete_user_without_permissions_forbidden(self):
        """
        Test for API delete when user don't have any permissions and
        don't have access to the specified laboratory/organization
        """
        delete_url = reverse('laboratory:api-shelfobject-delete', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id})
        self.client.logout()
        self.client.force_login(self.user3)
        response = self.client.delete(delete_url, data={'shelfobj': 1}, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_shelfobject_api_delete_anonymous_user_forbidden(self):
        """
        Test for API delete when anonymous user tries to access
        """
        delete_url = reverse('laboratory:api-shelfobject-delete', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id})
        self.client.logout()
        response = self.client.delete(delete_url, data={'shelfobj': 1}, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.client.force_login(self.user)

    def test_shelfobject_api_delete_wrong_key(self):
        """
        Test for API delete when the data is wrong
        """
        delete_url = reverse('laboratory:api-shelfobject-delete', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id})
        response = self.client.delete(delete_url, data={'shelfobj_wrong': 1}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_shelfobject_api_delete_wrong_content_type(self):
        """
        Test for API delete unsupported media type
        content_type = 'application/octet-stream'
        """
        delete_url = reverse('laboratory:api-shelfobject-delete', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id})
        response = self.client.delete(delete_url, data={'shelfobj': 1})
        self.assertEqual(response.status_code, 415)

    def test_shelfobject_observations_view_user_with_permissions_redirect(self):
        """
        Test for Shelf Object Observation view when user have permissions in their organization
        but don't have access to the specified laboratory/organization
        """
        view_url = reverse('laboratory:get_shelfobject_log', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk':1})
        self.client.logout()
        self.client.force_login(self.user2)
        response = self.client.get(view_url)
        self.assertEqual(response.status_code, 302)

    def test_shelfobject_observations_view_user_without_permissions_redirect(self):
        """
        Test for Shelf Object Observation view when user don't have any permissions and
        don't have access to the specified laboratory/organization
        """
        view_url = reverse('laboratory:get_shelfobject_log', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk':1})
        self.client.logout()
        self.client.force_login(self.user3)
        response = self.client.get(view_url)
        self.assertEqual(response.status_code, 302)

    def test_shelfobject_observations_view_anonymous_user_redirect(self):
        """
        Test for Shelf Object Observation view when anonymous user tries to access
        """
        view_url = reverse('laboratory:get_shelfobject_log', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk':1})
        self.client.logout()
        response = self.client.get(view_url)
        self.assertEqual(response.status_code, 302)

    def test_shelfobject_observations_view_template(self):
        """
        Test for Shelf Object Observation view to check if template being loaded is the correct one
        """
        view_url = reverse('laboratory:get_shelfobject_log', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk':1})
        response = self.client.get(view_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0].template_name, 'laboratory/shelfobject/shelfobject_observations.html')

    def test_shelfobject_observations_view_required_tables(self):
        """
        Test for Shelf Object Observation view to check if the html elements
        for the tables and forms are in the template
        """
        view_url = reverse('laboratory:get_shelfobject_log', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1})
        response = self.client.get(view_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response=response, text='id="observationTable"')
        self.assertContains(response=response, text='data-modalid="status_modal"')
        self.assertContains(response=response, text='data-modalid="observation_modal"')

    def test_shelfobject_observations_view_urls (self):
        """
        Test for Shelf Object Observation view check if the urls of the objects are loaded correctly
        """
        view_url = reverse('laboratory:get_shelfobject_log',
                           kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1})
        response = self.client.get(view_url)
        observation_table_url = reverse('laboratory:api-shelfobject-list-comments',
                                        kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1})
        shelf_availability_information = reverse('laboratory:api-shelfobject-shelf-availability-information',
                                                 kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id})
        change_status = reverse('laboratory:api-shelfobject-create-status',
                                kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id})
        observation_url = f"observation_table: '{observation_table_url}'"
        shelf_url = f"shelf_availability_information: '{shelf_availability_information}'"
        status_url = f"change_status: '{change_status}'"
        self.assertEqual(response.status_code, 200)
        self.assertContains(response=response, text=observation_url)
        self.assertContains(response=response, text=shelf_url)
        self.assertContains(response=response, text=status_url)

    def test_shelfobject_observations_view_forms(self):
        """
        Test for Shelf Object Observation view to verify if the forms are loaded correctly into the template
        """
        view_url = reverse('laboratory:get_shelfobject_log',
                           kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1})
        response = self.client.get(view_url)
        self.assertContains(response=response, text='id="observation_form"')
        self.assertContains(response=response, text='id="status_form"')

    def test_delete_all_observations_without_deleting_shelf_object(self):
        """
        Test if deleting all observations of a shelf object don't delete the object itself.
        """
        ShelfObjectObservation.objects.filter(shelf_object=1).delete()
        self.assertTrue(ShelfObject.objects.filter(pk=1).exists())




