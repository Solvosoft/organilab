from django.test import tag

from laboratory.tests.selenium_tests.manage_organizations.base import (
    ManageOrganizationsSeleniumTest,
)
from organilab_test.tests.selenium_xpaths import select2_result


@tag("selenium")
class ProfileTabTest(ManageOrganizationsSeleniumTest):

    def test_change_profile_permission_group_by_org(self):
        """Test changing permission groups for a profile in an organization.

        Flow: Select org via iCheck -> Click 'By profile' tab -> Select
        profile in first Select2 -> Select permission group in second
        Select2 -> Save changes.

        GIF: docs/source/_static/gif/change_profile_permission_group_by_org.gif
        """
        path_list = self.select_organization + [
            {
                "path": "//*[@id='navbyprofile']",
                "sleep": 1,
            },
            {
                "path": "//*[@id='byprofile']//span[contains(@class, 'select2-selection')]",
                "sleep": 1,
            },
            {
                "path": select2_result(2),
            },
            {
                "path": "(//*[@id='byprofile']//span[contains(@class, 'select2-selection')])[last()]",
                "sleep": 1,
            },
            {
                "path": select2_result(3),
            },
            {
                "path": "//*[@id='savegroupsbyprofile']",
            },
        ]
        self.create_gif_process(path_list, "change_profile_permission_group_by_org")
