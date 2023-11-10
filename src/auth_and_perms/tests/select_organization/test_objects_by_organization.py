from auth_and_perms.tests.select_organization.base import ObjectsByOrganizationViewTest, \
    OrgDoesNotExists, WithoutOrg


class ObjectsByOrganizationViewTest1(ObjectsByOrganizationViewTest):
    """
    Organization exists
    Case 1: User is an organization member
    Case 2: User is not an organization member
    """

    def test_get_objects_by_org_case1(self):
        self.check_tests(user_in_org=True, status_code=200)

    def test_get_objects_by_org_case2(self):
        self.check_tests(self.user2, self.client2, status_code=403)


class ObjectsByOrganizationViewTest2(ObjectsByOrganizationViewTest, OrgDoesNotExists):
    """
    Organization does not exist
    Case 1: User is trying to get objects by not valid organization pk
    """

    def test_get_objects_by_org_case1(self):
        self.check_tests()


class ObjectsByOrganizationViewTest3(ObjectsByOrganizationViewTest, WithoutOrg):
    """
    Without organization
    Case 1: User is trying to get objects without organization pk parameter
    """

    def test_get_objects_by_org_case1(self):
        self.check_tests()
