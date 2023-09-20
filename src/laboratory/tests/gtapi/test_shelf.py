from laboratory.models import Shelf
from laboratory.tests.gtapi.base import ShelfViewTest

class ShelfViewTestOrgCanManageLab(ShelfViewTest):

    def setUp(self):
        super().setUp()

class ShelfViewTestOrgCannotManageLab(ShelfViewTest):

    def setUp(self):
        super().setUp()
        self.lab = self.lab2_org2
        self.data.update({
            "laboratory": self.lab.pk
        })

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
        results = self.check_tests(response, 200, True, True, False)

        if results:
            self.assertEqual(results[0]["id"], shelf.first().pk)

    def test_get_shelf_by_shelfobject_case2(self):
        """
            Case 2 - User 2 has access in organization but not in this laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.user = self.user2
        self.client = self.client2
        response = self.client.get(self.url, data=self.data)
        self.check_tests(response, 400, True, False)


    def test_get_shelf_by_shelfobject_case3(self):
        """
            Case 3 - User 3 has access in this laboratory but not in this organization

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.user = self.user3
        self.client = self.client3
        response = self.client.get(self.url, data=self.data)
        self.check_tests(response, 400, True, False)

    def test_get_shelf_by_shelfobject_case4(self):
        """
            Case 4 - User 4 does not have access in this organization and laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.user = self.user4
        self.client = self.client4
        response = self.client.get(self.url, data=self.data)
        self.check_tests(response, 400, True, False)

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
        self.check_tests(response, 400, True, True)

    def test_get_shelf_by_shelfobject_case2(self):
        """
            Case 2 - User 2 has access in organization but not in this laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.user = self.user2
        self.client = self.client2
        response = self.client.get(self.url, data=self.data)
        self.check_tests(response, 400, True, False)

    def test_get_shelf_by_shelfobject_case3(self):
        """
            Case 3 - User 3 has access in this laboratory but not in this organization

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.user = self.user3
        self.client = self.client3
        response = self.client.get(self.url, data=self.data)
        self.check_tests(response, 400, True, False)

    def test_get_shelf_by_shelfobject_case4(self):
        """
            Case 4 - User 4 does not have access in this organization and laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.user = self.user4
        self.client = self.client4
        response = self.client.get(self.url, data=self.data)
        self.check_tests(response, 400, True, False)

class ShelfViewTest3(ShelfViewTestOrgCanManageLab):
    """
        * Organization can manage this laboratory
        * Without related furniture(relfield)
    """

    def setUp(self):
        super().setUp()
        del self.data["relfield"]

    def test_get_shelf_by_shelfobject_case1(self):
        """
            Case 1 - User 1 has access in this organization and laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user has permission to access in this organization and laboratory.
        4) Check if 'results' key return some object from response serializer data.
        5) Check if shelf pk result is equal to expected shelf pk.
        """
        response = self.client.get(self.url, data=self.data)
        self.check_tests(response, 200, True, True, False)


    def test_get_shelf_by_shelfobject_case2(self):
        """
            Case 2 - User 2 has access in organization but not in this laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.user = self.user2
        self.client = self.client2
        response = self.client.get(self.url, data=self.data)
        self.check_tests(response, 400, True, False)


    def test_get_shelf_by_shelfobject_case3(self):
        """
            Case 3 - User 3 has access in this laboratory but not in this organization

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.user = self.user3
        self.client = self.client3
        response = self.client.get(self.url, data=self.data)
        self.check_tests(response, 400, True, False)

    def test_get_shelf_by_shelfobject_case4(self):
        """
            Case 4 - User 4 does not have access in this organization and laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.user = self.user4
        self.client = self.client4
        response = self.client.get(self.url, data=self.data)
        self.check_tests(response, 400, True, False)

class ShelfViewTest4(ShelfViewTestOrgCannotManageLab):
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
        self.check_tests(response, 400, False, False)

    def test_get_shelf_by_shelfobject_case2(self):
        """
            Case 2 - User 2 has access in organization but not in this laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.user = self.user2
        self.client = self.client2
        response = self.client.get(self.url, data=self.data)
        self.check_tests(response, 400, False, False)

    def test_get_shelf_by_shelfobject_case3(self):
        """
            Case 3 - User 3 has access in this laboratory but not in this organization

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.user = self.user3
        self.client = self.client3
        response = self.client.get(self.url, data=self.data)
        self.check_tests(response, 400, False, False)

    def test_get_shelf_by_shelfobject_case4(self):
        """
            Case 4 - User 4 does not have access in this organization and laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.user = self.user4
        self.client = self.client4
        response = self.client.get(self.url, data=self.data)
        self.check_tests(response, 400, False, False)

class ShelfViewTest5(ShelfViewTestOrgCannotManageLab):
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
        self.check_tests(response, 400, False, False)

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
        self.check_tests(response, 400, False, False)

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
        self.check_tests(response, 400, False, False)

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
        self.check_tests(response, 400, False, False)

class ShelfViewTest6(ShelfViewTestOrgCannotManageLab):
    """
        * Organization cannot manage this laboratory
        * Without related furniture(relfield)
    """

    def setUp(self):
        super().setUp()
        del self.data["relfield"]

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
        self.check_tests(response, 400, False, False)

    def test_get_shelf_by_shelfobject_case2(self):
        """
            Case 2 - User 2 has access in organization but not in this laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.user = self.user2
        self.client = self.client2
        response = self.client.get(self.url, data=self.data)
        self.check_tests(response, 400, False, False)

    def test_get_shelf_by_shelfobject_case3(self):
        """
            Case 3 - User 3 has access in this laboratory but not in this organization

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.user = self.user3
        self.client = self.client3
        response = self.client.get(self.url, data=self.data)
        self.check_tests(response, 400, False, False)

    def test_get_shelf_by_shelfobject_case4(self):
        """
            Case 4 - User 4 does not have access in this organization and laboratory

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if organization can change this laboratory.
        3) Check if user does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """
        self.user = self.user4
        self.client = self.client4
        response = self.client.get(self.url, data=self.data)
        self.check_tests(response, 400, False, False)
