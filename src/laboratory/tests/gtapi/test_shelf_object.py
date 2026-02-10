from laboratory.models import Shelf
from laboratory.tests.gtapi.base import (
    ShelfObjectViewTestOrgCanManageLab,
    ShelfObjectViewTest,
    WithoutOrg,
    WithoutLab,
    OrgDoesNotExists,
    LabDoesNotExists,
    OrgCannotManageLab,
)


class ShelfObjectViewTest1(ShelfObjectViewTestOrgCanManageLab):
    """
    * Organization can manage this laboratory
    * With required data
    """

    def setUp(self):
        super().setUp()

    def test_get_available_container_by_lab_and_shelf_case1(self):
        self.get_available_container_by_lab_and_shelf(
            self.user1, self.client1,
            user_access=True, status_code=200, results_data=False, same_lab=True
        )

    def test_get_available_container_by_lab_and_shelf_case2(self):
        self.get_available_container_by_lab_and_shelf(
            self.user2, self.client2, same_lab=True
        )

    def test_get_available_container_by_lab_and_shelf_case3(self):
        self.get_available_container_by_lab_and_shelf(
            self.user3, self.client3, same_lab=True
        )

    def test_get_available_container_by_lab_and_shelf_case4(self):
        self.get_available_container_by_lab_and_shelf(
            self.user4, self.client4, same_lab=True
        )


class ShelfObjectViewTest2(ShelfObjectViewTestOrgCanManageLab):
    """
    * Organization can manage this laboratory
    * Without required data
    """

    def setUp(self):
        super().setUp()
        self.data = {}

    def test_get_available_container_by_lab_and_shelf_case1(self):
        self.get_available_container_by_lab_and_shelf(user_access=True)

    def test_get_available_container_by_lab_and_shelf_case2(self):
        self.get_available_container_by_lab_and_shelf(self.user2, self.client2)

    def test_get_available_container_by_lab_and_shelf_case3(self):
        self.get_available_container_by_lab_and_shelf(self.user3, self.client3)

    def test_get_available_container_by_lab_and_shelf_case4(self):
        self.get_available_container_by_lab_and_shelf(self.user4, self.client4)


class ShelfObjectViewTest3(ShelfObjectViewTestOrgCanManageLab):
    """
    * Organization can manage this laboratory
    * Shelf is in other laboratory in this same organization
    """

    def setUp(self):
        super().setUp()
        self.shelf = Shelf.objects.get(pk=6)
        self.data.update({"shelf": self.shelf.pk})

    def test_get_available_container_by_lab_and_shelf_case1(self):
        self.get_available_container_by_lab_and_shelf(user_access=True)

    def test_get_available_container_by_lab_and_shelf_case2(self):
        self.get_available_container_by_lab_and_shelf(self.user2, self.client2)

    def test_get_available_container_by_lab_and_shelf_case3(self):
        self.get_available_container_by_lab_and_shelf(self.user3, self.client3)

    def test_get_available_container_by_lab_and_shelf_case4(self):
        self.get_available_container_by_lab_and_shelf(self.user4, self.client4)


class ShelfObjectViewTest4(ShelfObjectViewTestOrgCanManageLab):
    """
    * Organization can manage this laboratory
    * Shelf is in other laboratory in other organization
    """

    def setUp(self):
        super().setUp()
        self.org = self.org2
        self.lab = self.lab2_org2
        self.data.update({"organization": self.org.pk, "laboratory": self.lab.pk})

    def test_get_available_container_by_lab_and_shelf_case1(self):
        self.get_available_container_by_lab_and_shelf(user_access=True)

    def test_get_available_container_by_lab_and_shelf_case2(self):
        self.get_available_container_by_lab_and_shelf(self.user2, self.client2)

    def test_get_available_container_by_lab_and_shelf_case3(self):
        self.get_available_container_by_lab_and_shelf(self.user3, self.client3)

    def test_get_available_container_by_lab_and_shelf_case4(self):
        self.get_available_container_by_lab_and_shelf(self.user4, self.client4)


class ShelfObjectViewTest5(ShelfObjectViewTest, OrgCannotManageLab):
    """
    * Organization cannot manage this laboratory
    * With required data
    """

    def setUp(self):
        super().setUp()

    def test_get_available_container_by_lab_and_shelf_case1(self):
        self.get_available_container_by_lab_and_shelf()

    def test_get_available_container_by_lab_and_shelf_case2(self):
        self.get_available_container_by_lab_and_shelf(self.user2, self.client2)

    def test_get_available_container_by_lab_and_shelf_case3(self):
        self.get_available_container_by_lab_and_shelf(self.user3, self.client3)

    def test_get_available_container_by_lab_and_shelf_case4(self):
        self.get_available_container_by_lab_and_shelf(self.user4, self.client4)


class ShelfObjectViewTest6(ShelfObjectViewTest, OrgCannotManageLab):
    """
    * Organization cannot manage this laboratory
    * Without required data
    """

    def setUp(self):
        super().setUp()
        self.data = {}

    def test_get_available_container_by_lab_and_shelf_case1(self):
        self.get_available_container_by_lab_and_shelf()

    def test_get_available_container_by_lab_and_shelf_case2(self):
        self.get_available_container_by_lab_and_shelf(self.user2, self.client2)

    def test_get_available_container_by_lab_and_shelf_case3(self):
        self.get_available_container_by_lab_and_shelf(self.user3, self.client3)

    def test_get_available_container_by_lab_and_shelf_case4(self):
        self.get_available_container_by_lab_and_shelf(self.user4, self.client4)


class ShelfObjectViewTest7(ShelfObjectViewTest, OrgCannotManageLab):
    """
    * Organization can manage this laboratory
    * Shelf is in other laboratory in this same organization
    """

    def setUp(self):
        super().setUp()
        self.shelf = Shelf.objects.get(pk=6)
        self.data.update({"shelf": self.shelf.pk})

    def test_get_available_container_by_lab_and_shelf_case1(self):
        self.get_available_container_by_lab_and_shelf()

    def test_get_available_container_by_lab_and_shelf_case2(self):
        self.get_available_container_by_lab_and_shelf(self.user2, self.client2)

    def test_get_available_container_by_lab_and_shelf_case3(self):
        self.get_available_container_by_lab_and_shelf(self.user3, self.client3)

    def test_get_available_container_by_lab_and_shelf_case4(self):
        self.get_available_container_by_lab_and_shelf(self.user4, self.client4)


class ShelfObjectViewTest8(ShelfObjectViewTest, WithoutOrg):
    """
    * Without organization param
    """

    def test_get_available_container_by_lab_and_shelf_case1(self):
        self.get_available_container_by_lab_and_shelf(same_lab=True)

    def test_get_available_container_by_lab_and_shelf_case2(self):
        self.get_available_container_by_lab_and_shelf(
            self.user2, self.client2, same_lab=True
        )

    def test_get_available_container_by_lab_and_shelf_case3(self):
        self.get_available_container_by_lab_and_shelf(
            self.user3, self.client3, same_lab=True
        )

    def test_get_available_container_by_lab_and_shelf_case4(self):
        self.get_available_container_by_lab_and_shelf(
            self.user4, self.client4, same_lab=True
        )


class ShelfObjectViewTest9(ShelfObjectViewTest, WithoutLab):
    """
    * Without laboratory param
    """

    def test_get_available_container_by_lab_and_shelf_case1(self):
        self.get_available_container_by_lab_and_shelf()

    def test_get_available_container_by_lab_and_shelf_case2(self):
        self.get_available_container_by_lab_and_shelf(self.user2, self.client2)

    def test_get_available_container_by_lab_and_shelf_case3(self):
        self.get_available_container_by_lab_and_shelf(self.user3, self.client3)

    def test_get_available_container_by_lab_and_shelf_case4(self):
        self.get_available_container_by_lab_and_shelf(self.user4, self.client4)


class ShelfObjectViewTest10(ShelfObjectViewTest, WithoutOrg, WithoutLab):
    """
    * Without organization and laboratory params
    """

    def test_get_available_container_by_lab_and_shelf_case1(self):
        self.get_available_container_by_lab_and_shelf()

    def test_get_available_container_by_lab_and_shelf_case2(self):
        self.get_available_container_by_lab_and_shelf(self.user2, self.client2)

    def test_get_available_container_by_lab_and_shelf_case3(self):
        self.get_available_container_by_lab_and_shelf(self.user3, self.client3)

    def test_get_available_container_by_lab_and_shelf_case4(self):
        self.get_available_container_by_lab_and_shelf(self.user4, self.client4)


class ShelfObjectViewTest11(ShelfObjectViewTest, OrgDoesNotExists, LabDoesNotExists):
    """
    * Organization and laboratory do not exist
    """

    def test_get_available_container_by_lab_and_shelf_case1(self):
        self.get_available_container_by_lab_and_shelf()

    def test_get_available_container_by_lab_and_shelf_case2(self):
        self.get_available_container_by_lab_and_shelf(self.user2, self.client2)

    def test_get_available_container_by_lab_and_shelf_case3(self):
        self.get_available_container_by_lab_and_shelf(self.user3, self.client3)

    def test_get_available_container_by_lab_and_shelf_case4(self):
        self.get_available_container_by_lab_and_shelf(self.user4, self.client4)


class ShelfObjectViewTest12(ShelfObjectViewTest, LabDoesNotExists):
    """
    * Laboratory does not exist
    """

    def test_get_available_container_by_lab_and_shelf_case1(self):
        self.get_available_container_by_lab_and_shelf()

    def test_get_available_container_by_lab_and_shelf_case2(self):
        self.get_available_container_by_lab_and_shelf(self.user2, self.client2)

    def test_get_available_container_by_lab_and_shelf_case3(self):
        self.get_available_container_by_lab_and_shelf(self.user3, self.client3)

    def test_get_available_container_by_lab_and_shelf_case4(self):
        self.get_available_container_by_lab_and_shelf(self.user4, self.client4)


class ShelfObjectViewTest13(ShelfObjectViewTest, OrgDoesNotExists):
    """
    * Organization does not exist
    """

    def test_get_available_container_by_lab_and_shelf_case1(self):
        self.get_available_container_by_lab_and_shelf(same_lab=True)

    def test_get_available_container_by_lab_and_shelf_case2(self):
        self.get_available_container_by_lab_and_shelf(
            self.user2, self.client2, same_lab=True,
        )

    def test_get_available_container_by_lab_and_shelf_case3(self):
        self.get_available_container_by_lab_and_shelf(
            self.user3, self.client3, same_lab=True
        )

    def test_get_available_container_by_lab_and_shelf_case4(self):
        self.get_available_container_by_lab_and_shelf(
            self.user4, self.client4, same_lab=True
        )
