import json
from django.urls import reverse

from auth_and_perms.organization_utils import organization_can_change_laboratory
from laboratory.models import Furniture, ShelfObject, Shelf
from laboratory.tests.gtapi.base import TestCaseBase
from laboratory.utils import check_user_access_kwargs_org_lab


class ShelfViewTest(TestCaseBase):
    def setUp(self):
        super().setUp()
        self.user = self.user1_org1
        self.lab = self.lab1_org1
        self.org = self.org1
        self.furniture = Furniture.objects.get(pk=1)
        self.shelfobject = ShelfObject.objects.get(pk=1)
        self.url = reverse("shelf-list")
        self.data = {
            "shelfobject": self.shelfobject.pk,
            "laboratory": self.lab.pk,
            "organization": self.org.pk,
            "relfield": self.furniture.pk,
            "page": 1
        }
        self.client = self.client1_org1


class ShelfViewTestUserWithPermissions(ShelfViewTest):
    """
        Move Form - Laboratory View
    """

    def setUp(self):
        super().setUp()



    def test_get_shelf_by_shelfobject_case1(self):
        """
            Case 1 - User 1 has access in this organization and laboratory

        CHECK TESTS
        1) Check response status code equal to 200.
        2) Check if organization can change this laboratory.
        3) Check if user has permission to access in this organization and laboratory.
        4) Check if 'results' key return some object from response serializer data.
        5) Check if shelf pk result is equal to expected shelf pk.
        """

        shelf = Shelf.objects.filter(furniture=self.data["relfield"]).exclude(pk=self.shelfobject.shelf.pk)
        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, 200)

        has_permission = organization_can_change_laboratory(self.lab, self.org)
        check_user_access = check_user_access_kwargs_org_lab(self.org.pk,
                                                             self.lab.pk, self.user)
        self.assertTrue(has_permission)
        self.assertTrue(check_user_access)

        if response.content:
            response_data = json.loads(response.content)
            self.assertTrue(response_data['results'])
            self.assertEqual(response_data['results'][0]["id"], shelf.first().pk)

    def test_get_shelf_by_shelfobject_case2(self):
        """
            Case 2 - User 1 has access in organization but not in this laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.shelfobject = ShelfObject.objects.get(pk=2)
        self.furniture = Furniture.objects.get(pk=3)
        self.lab = self.lab2_org1
        self.data.update({
            "shelfobject": self.shelfobject.pk,
            "relfield": self.furniture.pk,
            "laboratory": self.lab.pk
        })

        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)

        has_permission = organization_can_change_laboratory(self.lab, self.org)
        check_user_access = check_user_access_kwargs_org_lab(self.org.pk,
                                                             self.lab.pk, self.user)
        self.assertTrue(has_permission)
        self.assertFalse(check_user_access)

        if response.content:
            response_data = json.loads(response.content)
            self.assertTrue("results" not in response_data)

