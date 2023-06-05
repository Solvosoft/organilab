from django.urls import reverse

from laboratory.models import Shelf
from laboratory.tests.utils import BaseLaboratorySetUpTest, ShelfObjectSetUp
import json

from laboratory.utils import check_user_access_kwargs_org_lab, get_laboratories_by_user_profile


class ShelfViewTest(BaseLaboratorySetUpTest):

    def test_update_shelf(self):
        shelf = Shelf.objects.first()
        url = reverse("laboratory:shelf_edit", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": shelf.pk,
                                                       "row": shelf.row(), "col": shelf.col()})

        #Checking by method get if initial data shelf exists
        response_get = self.client.get(url, data={'furniture': shelf.furniture.pk}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "Primer Estante")

        # Updating shelf
        data = {
            "shelf--name": "Estante central",
            "shelf--type": 74,
            "shelf--furniture": 1,
            "shelf--color": "#73879C",
            "shelf--row": 1,
            "shelf--col": 0,
            "shelf--in_where_laboratory": self.lab.pk,
            "shelf--discard": False,
            "shelf--quantity": 3,
            "shelf--description": "Estante de muestras",
            "shelf--measurement_unit": 59
        }
        response_post = self.client.post(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response_post.status_code, 200)
        self.assertIn("Estante central", json.loads(response_post.content)['content']['inner-fragments']['#shelfmodalbody'])

    def test_create_shelf(self):
        data = {
            "shelf--name": "Muestras",
            "shelf--type": 72,
            "shelf--furniture": 1,
            "shelf--color": "#73879C",
            "shelf--col": 0,
            "shelf--row": 2,
            "shelf--discard": False,
            "shelf--quantity": 3,
            "shelf--description": "Estante de muestras",
            "shelf--measurement_unit": 59,
            "shelf--in_where_laboratory": self.lab.pk,
        }
        url = reverse("laboratory:shelf_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIn("Muestras", list(Shelf.objects.values_list("name", flat=True)))
        self.assertEqual(response.status_code, 200)

    def test_delete_shelf(self):
        shelf = Shelf.objects.get(name="Noveno Estante")
        url = reverse("laboratory:shelf_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": shelf.pk,
                                                         "row": shelf.row(), "col": shelf.col()})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Noveno Estante", list(Shelf.objects.values_list("name", flat=True)))

    def test_add_shelf_type_catalog(self):
        url = reverse("laboratory:add_shelf_type_catalog")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class ShelfAvailabilityInformationViewTest(ShelfObjectSetUp):

    def test_shelf_availability_information_user_with_permissions(self):
        """
        #EXPECTED CASE

        This test does an availability information shelf request by get method and action 'shelf_availability_information'
        located in laboratory/api/shelfobject.py --> ShelfObjectViewSet generic view set class.

        CHECK TESTS
        1) Check response status code equal to 200.
        2) Check if user has access permission to request and view this shelf information.
        3) Check if shelf name is equal to returned name in response content.
        4) Check if pk laboratory related to this shelf is equal to declared pk laboratory in url.
        """

        shelf = Shelf.objects.get(pk=1)
        url = reverse("laboratory:api-shelfobject-shelf-availability-information", kwargs={"org_pk": self.org1.pk, "lab_pk": self.lab1_org1.pk})
        data = {
            "shelf": shelf.pk
        }
        response = self.client1_org1.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(check_user_access_kwargs_org_lab(self.org1.pk, self.lab1_org1.pk, self.user1_org1))
        self.assertIn(shelf.name, json.loads(response.content)['name'])
        self.assertEqual(shelf.furniture.labroom.laboratory.pk, self.lab1_org1.pk)


    def test_get_shelf_availability_information_user_without_permissions(self):
        """
        #UNEXPECTED CASE, BUT POSSIBLE(User to other organization try to get shelf information)

        This test does an availability information shelf request by get method and action 'shelf_availability_information'
        located in laboratory/api/shelfobject.py --> ShelfObjectViewSet generic view set class.

        CHECK TESTS
        1) Check response status code equal to 403.
        2) Check if user has access permission to request and view this shelf information.
        3) Check if response content return an error detail.
        4) Check if pk laboratory related to this shelf is in laboratories list by user.
        """
        shelf = Shelf.objects.get(pk=1)
        url = reverse("laboratory:api-shelfobject-shelf-availability-information",
                      kwargs={"org_pk": self.org1.pk, "lab_pk": self.lab1_org1.pk})
        data = {
            "shelf": shelf.pk
        }
        response = self.client2_org2.get(url, data=data)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(check_user_access_kwargs_org_lab(self.org1.pk, self.lab1_org1.pk, self.user2_org2))
        self.assertIn('detail', json.loads(response.content))
        self.assertNotIn(shelf.furniture.labroom.laboratory.pk, get_laboratories_by_user_profile(self.user2_org2, self.org1.pk))