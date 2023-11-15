from auth_and_perms.tests.select_organization.base import \
    OrganizationButtonsByUserViewTest, WithoutOrg, OrgDoesNotExists


class OrganizationButtonsByUserViewTest1(OrganizationButtonsByUserViewTest):
    """
    Organization exists
    Case 1: User is an organization member
    Case 2: User is not an organization member with permissions rols in this organization(fake data but possible case)
    Case 3: User is an organization member but without permissions rols
    Case 4: User is not an organization member but without permissions rols
    """

    def test_get_organization_buttons_by_user_case1(self):
        self.check_tests(user_in_org=True, status_code=200, can_view_actions_buttons=True)

    def test_get_organization_buttons_by_user_case2(self):
        self.check_tests(self.user2, self.client2, status_code=403)

    def test_get_organization_buttons_by_user_case3(self):
        self.check_tests(user_in_org=True, user=self.user3, client=self.client3, status_code=200)

    def test_get_organization_buttons_by_user_case4(self):
        self.check_tests(self.user4, self.client4, status_code=403)


class OrganizationButtonsByUserViewTest2(OrganizationButtonsByUserViewTest, WithoutOrg):
    """
    Without organization
    Case 1: User is trying to get action buttons without organization pk parameter
    """

    def test_get_organization_buttons_by_user_case1(self):
        self.check_tests()


class ObjectsByOrganizationViewTest2(OrganizationButtonsByUserViewTest, OrgDoesNotExists):
    """
    Organization does not exist
    Case 1: User is trying to get action buttons by not valid organization pk
    """

    def test_get_organization_buttons_by_user_case1(self):
        self.check_tests()
