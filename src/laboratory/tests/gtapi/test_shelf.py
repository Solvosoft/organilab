import json
from django.urls import reverse

from auth_and_perms.organization_utils import organization_can_change_laboratory
from laboratory.models import Furniture, ShelfObject, Shelf
from laboratory.tests.gtapi.base import TestCaseBase
from laboratory.utils import check_user_access_kwargs_org_lab


class ShelfViewTest(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.furniture = Furniture.objects.get(pk=1)
        self.shelfobject = ShelfObject.objects.get(pk=1)
        self.url = reverse("shelf-list")
        self.user = self.user1
        self.client = self.client1

class ShelfViewTestOrgCanManageLab(ShelfViewTest):

    def setUp(self):
        super().setUp()
        self.lab = self.lab1_org1
        self.org = self.org1
        self.data = {
            "shelfobject": self.shelfobject.pk,
            "laboratory": self.lab.pk,
            "organization": self.org.pk,
            "relfield": self.furniture.pk,
            "page": 1
        }


class ShelfViewTestOrgCannotManageLab(ShelfViewTest):

    def setUp(self):
        super().setUp()
        self.lab = self.lab2_org2
        self.org = self.org1
        self.data = {
            "shelfobject": self.shelfobject.pk,
            "laboratory": self.lab.pk,
            "organization": self.org.pk,
            "relfield": self.furniture.pk,
            "page": 1
        }


class ShelfViewTest1(ShelfViewTestOrgCanManageLab):
    """
        * Organization can manage this laboratory
        * With required data
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
            Case 2 - User 2 has access in organization but not in this laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.client = self.client2
        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)

        has_permission = organization_can_change_laboratory(self.lab, self.org)
        check_user_access = check_user_access_kwargs_org_lab(self.org.pk,
                                                             self.lab.pk, self.user2)
        self.assertTrue(has_permission)
        self.assertFalse(check_user_access)

        if response.content:
            response_data = json.loads(response.content)
            self.assertTrue("results" not in response_data)

    def test_get_shelf_by_shelfobject_case3(self):
        """
            Case 3 - User 3 has access in this laboratory but not in this organization

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.client = self.client3
        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)

        has_permission = organization_can_change_laboratory(self.lab, self.org)
        check_user_access = check_user_access_kwargs_org_lab(self.org.pk,
                                                             self.lab.pk, self.user3)
        self.assertTrue(has_permission)
        self.assertFalse(check_user_access)

        if response.content:
            response_data = json.loads(response.content)
            self.assertTrue("results" not in response_data)

    def test_get_shelf_by_shelfobject_case4(self):
        """
            Case 4 - User 4 does not have access in this organization and laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.client = self.client4
        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)

        has_permission = organization_can_change_laboratory(self.lab, self.org)
        check_user_access = check_user_access_kwargs_org_lab(self.org.pk,
                                                             self.lab.pk, self.user4)
        self.assertTrue(has_permission)
        self.assertFalse(check_user_access)

        if response.content:
            response_data = json.loads(response.content)
            self.assertTrue("results" not in response_data)

class ShelfViewTest2(ShelfViewTestOrgCanManageLab):
    """
        * Organization can manage this laboratory
        * Without required data
    """

    def setUp(self):
        super().setUp()
        self.data = {}

    def test_get_shelf_by_shelfobject_case1(self):
        """
            Case 1 - User 1 has access in this organization and laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user has permission to access in this organization and laboratory.
        4) Check if 'results' key return some object from response serializer data.
        """

        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)

        has_permission = organization_can_change_laboratory(self.lab, self.org)
        check_user_access = check_user_access_kwargs_org_lab(self.org.pk,
                                                             self.lab.pk, self.user)
        self.assertTrue(has_permission)
        self.assertTrue(check_user_access)

        if response.content:
            response_data = json.loads(response.content)
            self.assertTrue('results' not in response_data)

    def test_get_shelf_by_shelfobject_case2(self):
        """
            Case 2 - User 2 has access in organization but not in this laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.client = self.client2
        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)

        has_permission = organization_can_change_laboratory(self.lab, self.org)
        check_user_access = check_user_access_kwargs_org_lab(self.org.pk,
                                                             self.lab.pk, self.user2)
        self.assertTrue(has_permission)
        self.assertFalse(check_user_access)

        if response.content:
            response_data = json.loads(response.content)
            self.assertTrue("results" not in response_data)

    def test_get_shelf_by_shelfobject_case3(self):
        """
            Case 3 - User 3 has access in this laboratory but not in this organization

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.client = self.client3
        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)

        has_permission = organization_can_change_laboratory(self.lab, self.org)
        check_user_access = check_user_access_kwargs_org_lab(self.org.pk,
                                                             self.lab.pk, self.user3)
        self.assertTrue(has_permission)
        self.assertFalse(check_user_access)

        if response.content:
            response_data = json.loads(response.content)
            self.assertTrue("results" not in response_data)

    def test_get_shelf_by_shelfobject_case4(self):
        """
            Case 4 - User 4 does not have access in this organization and laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.client = self.client4
        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)

        has_permission = organization_can_change_laboratory(self.lab, self.org)
        check_user_access = check_user_access_kwargs_org_lab(self.org.pk,
                                                             self.lab.pk, self.user4)
        self.assertTrue(has_permission)
        self.assertFalse(check_user_access)

        if response.content:
            response_data = json.loads(response.content)
            self.assertTrue("results" not in response_data)

class ShelfViewTest3(ShelfViewTestOrgCannotManageLab):
    """
        * Organization cannot manage this laboratory
        * With required data
    """

    def setUp(self):
        super().setUp()

    def test_get_shelf_by_shelfobject_case1(self):
        """
            Case 1 - User 1 has access in this organization and laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key return some object from response serializer data.
        """
        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)

        has_permission = organization_can_change_laboratory(self.lab, self.org)
        check_user_access = check_user_access_kwargs_org_lab(self.org.pk,
                                                             self.lab.pk, self.user)
        self.assertFalse(has_permission)
        self.assertFalse(check_user_access)

        if response.content:
            response_data = json.loads(response.content)
            self.assertTrue("results" not in response_data)

    def test_get_shelf_by_shelfobject_case2(self):
        """
            Case 2 - User 2 has access in organization but not in this laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.client = self.client2
        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)

        has_permission = organization_can_change_laboratory(self.lab, self.org)
        check_user_access = check_user_access_kwargs_org_lab(self.org.pk,
                                                             self.lab.pk, self.user2)
        self.assertFalse(has_permission)
        self.assertFalse(check_user_access)

        if response.content:
            response_data = json.loads(response.content)
            self.assertTrue("results" not in response_data)

    def test_get_shelf_by_shelfobject_case3(self):
        """
            Case 3 - User 3 has access in this laboratory but not in this organization

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.client = self.client3
        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)

        has_permission = organization_can_change_laboratory(self.lab, self.org)
        check_user_access = check_user_access_kwargs_org_lab(self.org.pk,
                                                             self.lab.pk, self.user3)
        self.assertFalse(has_permission)
        self.assertFalse(check_user_access)

        if response.content:
            response_data = json.loads(response.content)
            self.assertTrue("results" not in response_data)

    def test_get_shelf_by_shelfobject_case4(self):
        """
            Case 4 - User 4 does not have access in this organization and laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.client = self.client4
        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)

        has_permission = organization_can_change_laboratory(self.lab, self.org)
        check_user_access = check_user_access_kwargs_org_lab(self.org.pk,
                                                             self.lab.pk, self.user4)
        self.assertFalse(has_permission)
        self.assertFalse(check_user_access)

        if response.content:
            response_data = json.loads(response.content)
            self.assertTrue("results" not in response_data)

class ShelfViewTest4(ShelfViewTestOrgCannotManageLab):
    """
        * Organization cannot manage this laboratory
        * Without required data
    """

    def setUp(self):
        super().setUp()
        self.data = {}

    def test_get_shelf_by_shelfobject_case1(self):
        """
            Case 1 - User 1 has access in this organization and laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key return some object from response serializer data.
        5) Check if shelf pk result is equal to expected shelf pk.
        """
        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)
        has_permission = organization_can_change_laboratory(self.lab, self.org)
        check_user_access = check_user_access_kwargs_org_lab(self.org.pk,
                                                             self.lab.pk, self.user)
        self.assertFalse(has_permission)
        self.assertFalse(check_user_access)

        if response.content:
            response_data = json.loads(response.content)
            self.assertTrue("results" not in response_data)

    def test_get_shelf_by_shelfobject_case2(self):
        """
            Case 2 - User 2 has access in organization but not in this laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.client = self.client2
        self.user = self.user2
        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)

        has_permission = organization_can_change_laboratory(self.lab, self.org)
        check_user_access = check_user_access_kwargs_org_lab(self.org.pk,
                                                             self.lab.pk, self.user)
        self.assertFalse(has_permission)
        self.assertFalse(check_user_access)

        if response.content:
            response_data = json.loads(response.content)
            self.assertTrue("results" not in response_data)

    def test_get_shelf_by_shelfobject_case3(self):
        """
            Case 3 - User 3 has access in this laboratory but not in this organization

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.client = self.client3
        self.user = self.user3
        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)

        has_permission = organization_can_change_laboratory(self.lab, self.org)
        check_user_access = check_user_access_kwargs_org_lab(self.org.pk,
                                                             self.lab.pk, self.user)
        self.assertFalse(has_permission)
        self.assertFalse(check_user_access)

        if response.content:
            response_data = json.loads(response.content)
            self.assertTrue("results" not in response_data)

    def test_get_shelf_by_shelfobject_case4(self):
        """
            Case 4 - User 4 does not have access in this organization and laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.client = self.client4
        self.user = self.user4
        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)

        has_permission = organization_can_change_laboratory(self.lab, self.org)
        check_user_access = check_user_access_kwargs_org_lab(self.org.pk,
                                                             self.lab.pk, self.user)
        self.assertFalse(has_permission)
        self.assertFalse(check_user_access)

        if response.content:
            response_data = json.loads(response.content)
            self.assertTrue("results" not in response_data)
