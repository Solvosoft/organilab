from auth_and_perms.tests.select_organization.base import OrganizationsByUserViewTest


class OrganizationsByUserViewTest1(OrganizationsByUserViewTest):

    def test_get_organizations_by_user_case1(self):
        self.check_tests(status_code=200)
