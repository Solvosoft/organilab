from laboratory.models import ShelfObject
from laboratory.tests.gtapi.base import (
    FurnitureViewTestOrgCanManageLab,
    FurnitureViewTest,
    OrgDoesNotExists,
    LabDoesNotExists,
    WithoutOrg,
    WithoutLab,
    OrgCannotManageLab,
)


class FurnitureViewTest1(FurnitureViewTestOrgCanManageLab):
    """
    * Organization can manage this laboratory
    * With required data
    """

    def setUp(self):
        super().setUp()

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject(
            user_access=True, status_code=200, results_data=False
        )

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)


class FurnitureViewTest2(FurnitureViewTestOrgCanManageLab):
    """
    * Organization can manage this laboratory
    * Without required data
    """

    def setUp(self):
        super().setUp()
        self.data = {}

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject(user_access=True)

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)


class FurnitureViewTest3(FurnitureViewTestOrgCanManageLab):
    """
    * Organization can manage this laboratory
    * Without related labroom(relfield)
    """

    def setUp(self):
        super().setUp()
        del self.data["relfield"]

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject(
            user_access=True, status_code=200, results_data=False
        )

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)


class FurnitureViewTest4(FurnitureViewTestOrgCanManageLab):
    """
    * Organization can manage this laboratory
    * With required data
    * Shelf Object is located to other laboratory in this same organization
    """

    def setUp(self):
        super().setUp()
        self.org = self.org2
        self.lab = self.lab2_org2
        self.shelfobject = ShelfObject.objects.get(pk=3)
        self.data.update(
            {
                "organization": self.org.pk,
                "laboratory": self.lab.pk,
                "shelfobject": self.shelfobject.pk,
            }
        )

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject(user_access=True, status_code=400)

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)


class FurnitureViewTest5(FurnitureViewTestOrgCanManageLab):
    """
    * Organization can manage this laboratory
    * With required data
    * Shelf Object is located to other laboratory in other organization
    """

    def setUp(self):
        super().setUp()
        self.shelfobject = ShelfObject.objects.get(pk=3)
        self.data.update({"shelfobject": self.shelfobject.pk})

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject(user_access=True, status_code=400)

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)


class FurnitureViewTest6(FurnitureViewTest, OrgCannotManageLab):
    """
    * Organization cannot manage this laboratory
    * With required data
    """

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)


class FurnitureViewTest7(FurnitureViewTest, OrgCannotManageLab):
    """
    * Organization cannot manage this laboratory
    * Without required data
    """

    def setUp(self):
        super().setUp()
        self.data = {}

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)


class FurnitureViewTest8(FurnitureViewTest, OrgCannotManageLab):
    """
    * Organization cannot manage this laboratory
    * Without related labroom(relfield)
    """

    def setUp(self):
        super().setUp()
        del self.data["relfield"]

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)


class FurnitureViewTest9(FurnitureViewTest, OrgCannotManageLab):
    """
    * Organization cannot manage this laboratory
    * With required data
    * Shelf Object is located to other laboratory in this same organization
    """

    def setUp(self):
        super().setUp()
        self.lab = self.lab2_org2
        self.shelfobject = ShelfObject.objects.get(pk=3)
        self.data.update(
            {"laboratory": self.lab.pk, "shelfobject": self.shelfobject.pk}
        )

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)


class FurnitureViewTest10(FurnitureViewTest, WithoutOrg):
    """
    * Without organization param
    """

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)


class FurnitureViewTest11(FurnitureViewTest, WithoutLab):
    """
    * Without laboratory param
    """

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)


class FurnitureViewTest12(FurnitureViewTest, WithoutOrg, WithoutLab):
    """
    * Without organization and laboratory params
    """

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)


class FurnitureViewTest13(FurnitureViewTest, OrgDoesNotExists, LabDoesNotExists):
    """
    * Organization and laboratory do not exist
    """

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)


class FurnitureViewTest14(FurnitureViewTest, LabDoesNotExists):
    """
    * Laboratory does not exists
    """

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)


class FurnitureViewTest15(FurnitureViewTest, OrgDoesNotExists):
    """
    * Organization does not exists
    """

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)
