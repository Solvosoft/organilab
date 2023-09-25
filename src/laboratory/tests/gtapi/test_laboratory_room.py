from laboratory.models import ShelfObject
from laboratory.tests.gtapi.base import LabRoomViewTestOrgCanManageLab, \
    LabRoomViewTestOrgCannotManageLab, LabRoomViewTestWithoutOrg, \
    LabRoomViewTestWithoutLab, LabRoomViewTestWithoutOrgLab, \
    LabRoomViewTestOrgLabDoNotExist, LabRoomViewTestLabDoesNotExists, \
    LabRoomViewTestOrgDoesNotExists


class LabRoomViewTest1(LabRoomViewTestOrgCanManageLab):
    """
        * Organization can manage this laboratory
        * With required data
    """

    def setUp(self):
        super().setUp()

    def test_get_labroom_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject(user_access=True, status_code=200, results_data=False)

    def test_get_labroom_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_labroom_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_labroom_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class LabRoomViewTest2(LabRoomViewTestOrgCanManageLab):
    """
        * Organization can manage this laboratory
        * Without required data
    """

    def setUp(self):
        super().setUp()
        self.data = {}

    def test_get_labroom_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject(user_access=True)

    def test_get_labroom_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_labroom_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_labroom_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class LabRoomViewTest3(LabRoomViewTestOrgCanManageLab):
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

    def test_get_labroom_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject(user_access=True)

    def test_get_labroom_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_labroom_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_labroom_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class LabRoomViewTest4(LabRoomViewTestOrgCanManageLab):
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

    def test_get_labroom_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject(user_access=True, status_code=400)

    def test_get_labroom_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_labroom_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_labroom_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class LabRoomViewTest5(LabRoomViewTestOrgCannotManageLab):
    """
        * Organization cannot manage this laboratory
        * With required data
    """

    def test_get_labroom_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_labroom_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_labroom_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_labroom_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class LabRoomViewTest6(LabRoomViewTestOrgCannotManageLab):
    """
        * Organization cannot manage this laboratory
        * Without required data
    """

    def setUp(self):
        super().setUp()
        self.data = {}

    def test_get_labroom_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_labroom_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_labroom_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_labroom_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class LabRoomViewTest7(LabRoomViewTestOrgCannotManageLab):
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

    def test_get_labroom_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_labroom_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_labroom_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_labroom_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class LabRoomViewTest8(LabRoomViewTestWithoutOrg):
    """
        * Without organization param
    """

    def test_get_labroom_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_labroom_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_labroom_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_labroom_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class LabRoomViewTest9(LabRoomViewTestWithoutLab):
    """
        * Without laboratory param
    """

    def test_get_labroom_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_labroom_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_labroom_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_labroom_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class LabRoomViewTest10(LabRoomViewTestWithoutOrgLab):
    """
        * Without organization and laboratory params
    """

    def test_get_labroom_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_labroom_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_labroom_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_labroom_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)

class LabRoomViewTest11(LabRoomViewTestOrgLabDoNotExist):
    """
        * Organization and laboratory do not exist
    """

    def test_get_labroom_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_labroom_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_labroom_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_labroom_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)


class LabRoomViewTest12(LabRoomViewTestLabDoesNotExists):
    """
        * Laboratory does not exists
    """

    def test_get_labroom_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_labroom_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_labroom_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_labroom_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)


class LabRoomViewTest13(LabRoomViewTestOrgDoesNotExists):
    """
        * Laboratory does not exists
    """

    def test_get_labroom_by_shelfobject_case1(self):
        self.get_obj_by_shelfobject()

    def test_get_labroom_by_shelfobject_case2(self):
        self.get_obj_by_shelfobject(self.user2, self.client2)

    def test_get_labroom_by_shelfobject_case3(self):
        self.get_obj_by_shelfobject(self.user3, self.client3)

    def test_get_labroom_by_shelfobject_case4(self):
        self.get_obj_by_shelfobject(self.user4, self.client4)
