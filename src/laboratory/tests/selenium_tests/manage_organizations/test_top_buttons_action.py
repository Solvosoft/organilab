from django.test import tag

from laboratory.tests.selenium_tests.manage_organizations.base import ManageOrganizationsSeleniumTest


@tag('selenium')
class TopButtonsActionTest(ManageOrganizationsSeleniumTest):

    def test_create_organization(self):
        """Test creating a new top-level organization via modal.

        Flow: Click 'Add organization' span -> Fill name in modal ->
        Submit modal.

        GIF: docs/source/_static/gif/create_org.gif
        """
        path_list = [
            {"path": "//span[@class='addOrgStructureEmpty']"},
            {
                "path": "//*[@id='addOrganizationmodal']//input[@id='id_name']",
                "sleep": 2,
            },
            {
                "path": "//*[@id='addOrganizationmodal']//input[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Sede Central",
            },
            {"path": self.get_submit_button_path("addOrganizationmodal")},
        ]
        self.create_gif_process(path_list, "create_org")
