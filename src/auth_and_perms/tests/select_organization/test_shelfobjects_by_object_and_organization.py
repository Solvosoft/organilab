from auth_and_perms.tests.select_organization.base import ShelfObjectsByObjectViewTest, \
    OrgDoesNotExists, ObjectDoesNotExists, WithoutObject, WithoutOrg


class ShelfObjectsByObjectViewTest1(ShelfObjectsByObjectViewTest):
    """
    Organization and object exists
    Case 1: User is an organization member
    Case 2: User is not an organization member
    """

    def test_get_shelfobjects_by_objects_and_org_case1(self):
        self.check_tests(user_in_org=True, status_code=200)

    def test_get_shelfobjects_by_objects_and_org_case2(self):
        self.check_tests(self.user2, self.client2, status_code=403)


class ShelfObjectsByObjectViewTest2(OrgDoesNotExists, ObjectDoesNotExists):
    """
    Organization and object do not exist
    Case 1: User is trying to get shelf objects by not valid organization and object pk
    """

    def test_get_shelfobjects_by_objects_and_org_case1(self):
        self.check_tests()


class ShelfObjectsByObjectViewTest3(ObjectDoesNotExists):
    """
    Object does not exist
    Case 1: User is trying to get shelf objects by not valid object pk
    """

    def test_get_shelfobjects_by_objects_and_org_case1(self):
        self.check_tests(user_in_org=True)


class ShelfObjectsByObjectViewTest4(ShelfObjectsByObjectViewTest, OrgDoesNotExists):
    """
    Organization does not exist
    Case 1: User is trying to get shelf objects by not valid organization pk
    """

    def test_get_shelfobjects_by_objects_and_org_case1(self):
        self.check_tests()


class ShelfObjectsByObjectViewTest5(WithoutOrg, WithoutObject):
    """
    Without organization and object
    Case 1: User is trying to get shelf objects without organization and object
    """

    def test_get_shelfobjects_by_objects_and_org_case1(self):
        self.check_tests()


class ShelfObjectsByObjectViewTest6(ShelfObjectsByObjectViewTest, WithoutOrg):
    """
    Without organization
    Case 1: User is trying to get shelf objects without organization
    """

    def test_get_shelfobjects_by_objects_and_org_case1(self):
        self.check_tests()


class ShelfObjectsByObjectViewTest7(WithoutObject):
    """
    Without object
    Case 1: User is trying to get shelf objects without object
    """

    def test_get_shelfobjects_by_objects_and_org_case1(self):
        self.check_tests()
