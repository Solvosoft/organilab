from django.test import tag

from laboratory.tests.selenium_tests.manage_organizations.base import ManageOrganizationsSeleniumTest


@tag('selenium')
class TopButtonsActionTest(ManageOrganizationsSeleniumTest):

    def test_create_organization(self):
        path_list = self.path_base + [
            {"path": ".//span[@class='addOrgStructureEmpty']"},
            {"path": ".//div[@id='addOrganizationmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div/div/input[@id='id_name']"},
            {"path": ".//div[@id='addOrganizationmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div/div/input[@id='id_name']",
                "extra_action": "setvalue", "value": "Sede Central"},
            {"path": self.get_submit_button_path("addOrganizationmodal")}
        ]
        self.create_gif_process(path_list, "create_org")
