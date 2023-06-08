from laboratory.models import ShelfObjectObservation, ShelfObject
from django.urls import reverse
from .test_shelfobject_api import ShelfObjectAPITest


class ShelfObjectObservationViewTest(ShelfObjectAPITest):

    def test_shelfobject_observations_view_user_with_permissions_redirect(self):
        """
        Test for Shelf Object Observation view when user have permissions in their organization
        but don't have access to the specified laboratory/organization
        """
        view_url = reverse('laboratory:get_shelfobject_log', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1})
        self.client.logout()
        self.client.force_login(self.user2)
        response = self.client.get(view_url)
        self.assertEqual(response.status_code, 302)

    def test_shelfobject_observations_view_user_without_permissions_redirect(self):
        """
        Test for Shelf Object Observation view when user don't have any permissions and
        don't have access to the specified laboratory/organization
        """
        view_url = reverse('laboratory:get_shelfobject_log', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1})
        self.client.logout()
        self.client.force_login(self.user3)
        response = self.client.get(view_url)
        self.assertEqual(response.status_code, 302)

    def test_shelfobject_observations_view_anonymous_user_redirect(self):
        """
        Test for Shelf Object Observation view when anonymous user tries to access
        """
        view_url = reverse('laboratory:get_shelfobject_log', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1})
        self.client.logout()
        response = self.client.get(view_url)
        self.assertEqual(response.status_code, 302)

    def test_shelfobject_observations_view_template(self):
        """
        Test for Shelf Object Observation view to check if template being loaded is the correct one
        """
        view_url = reverse('laboratory:get_shelfobject_log', kwargs={'org_pk': self.org_pk, 'lab_pk': self.lab.id, 'pk': 1})
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

    def test_shelfobject_observations_view_urls(self):
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