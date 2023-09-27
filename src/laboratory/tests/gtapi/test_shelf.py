from laboratory.models import ShelfObject
from laboratory.tests.gtapi.base import ShelfViewTestOrgCanManageLab, \
    ShelfViewTestOrgCannotManageLab, ShelfViewTestWithoutOrg, ShelfViewTestWithoutLab, \
    ShelfViewTestWithoutOrgLab, ShelfViewTestOrgLabDoNotExist, \
    ShelfViewTestLabDoesNotExists, ShelfViewTestOrgDoesNotExists, ShelfViewTest, \
    OrgDoesNotExists, LabDoesNotExists, WithoutOrg, WithoutLab


class ShelfViewTest1(ShelfViewTestOrgCanManageLab):
    """
        * Organization can manage this laboratory
        * With required data
    """

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject(user_access=True, status_code=200, results_data=False)

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class ShelfViewTest2(ShelfViewTestOrgCanManageLab):
    """
        * Organization can manage this laboratory
        * Without required data
    """

    def setUp(self):
        super().setUp()
        self.data = {}

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject(user_access=True)

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class ShelfViewTest3(ShelfViewTestOrgCanManageLab):
    """
        * Organization can manage this laboratory
        * Without related furniture(relfield)
    """

    def setUp(self):
        super().setUp()
        del self.data["relfield"]

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject(user_access=True, status_code=200, results_data=False)

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class ShelfViewTest4(ShelfViewTestOrgCanManageLab):
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
        self.data.update({
            "organization": self.org.pk,
            "laboratory": self.lab.pk,
            "shelfobject": self.shelfobject.pk
        })

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject(user_access=True, status_code=400)

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class ShelfViewTest5(ShelfViewTestOrgCanManageLab):
    """
        * Organization can manage this laboratory
        * With required data
        * Shelf Object is located to other laboratory in other organization
    """

    def setUp(self):
        super().setUp()
        self.shelfobject = ShelfObject.objects.get(pk=3)
        self.data.update({
            "shelfobject": self.shelfobject.pk
        })

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject(user_access=True, status_code=400)

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class ShelfViewTest6(ShelfViewTestOrgCannotManageLab):
    """
        * Organization cannot manage this laboratory
        * With required data
    """

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class ShelfViewTest7(ShelfViewTestOrgCannotManageLab):
    """
        * Organization cannot manage this laboratory
        * Without required data
    """

    def setUp(self):
        super().setUp()
        self.data = {}

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class ShelfViewTest8(ShelfViewTestOrgCannotManageLab):
    """
        * Organization cannot manage this laboratory
        * Without related furniture(relfield)
    """

    def setUp(self):
        super().setUp()
        del self.data["relfield"]

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class ShelfViewTest9(ShelfViewTestOrgCannotManageLab):
    """
        * Organization cannot manage this laboratory
        * With required data
        * Shelf Object is located to other laboratory in this same organization
    """

    def setUp(self):
        super().setUp()
        self.lab = self.lab2_org2
        self.shelfobject = ShelfObject.objects.get(pk=3)
        self.data.update({
            "laboratory": self.lab.pk,
            "shelfobject": self.shelfobject.pk
        })

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class ShelfViewTest10(ShelfViewTest, WithoutOrg):
    """
        * Without organization param
    """

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class ShelfViewTest11(ShelfViewTest, WithoutLab):
    """
        * Without laboratory param
    """

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class ShelfViewTest12(ShelfViewTest, WithoutOrg, WithoutLab):
    """
        * Without organization and laboratory params
    """

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class ShelfViewTest13(ShelfViewTest, OrgDoesNotExists, LabDoesNotExists):
    """
        * Organization and laboratory do not exist
    """

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class ShelfViewTest14(ShelfViewTest, LabDoesNotExists):
    """
        * Laboratory does not exists
    """

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)


class ShelfViewTest15(ShelfViewTest, OrgDoesNotExists):
    """
        * Organization does not exists
    """

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)
