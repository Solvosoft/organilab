from django.test import tag

from laboratory.tests.selenium_tests.manage_organizations.base import ManageOrganizationsSeleniumTest


@tag('selenium')
class ButtonBoxOrgTest(ManageOrganizationsSeleniumTest):

    def setUp(self):
        super().setUp()

        self.org_actions = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[5]/div/div/div[2]/ul/li[1]"},
            {"path": ".//div[@id='actionsmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div/div/span/span/span"},
        ]

        self.view_org_roles = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div[2]/ul/li[3]/a"}
        ]

    def test_deactivate_organization(self):
        path_list = self.org_actions + [
            {"path": "/html/body/span/span[@class='select2-dropdown select2-dropdown--below']/span[2]/ul/li[1]"},
            {"path": self.get_submit_button_path("actionsmodal")}
        ]
        self.create_gif_process(path_list, "deactivate_org")

    def test_clone_organization(self):
        path_list = self.org_actions + [
            {"path": "/html/body/span/span[@class='select2-dropdown select2-dropdown--below']/span[2]/ul/li[2]"},
            {"path": self.get_submit_button_path("actionsmodal")}
        ]
        self.create_gif_process(path_list, "clone_org")

    def test_change_organization_name(self):
        path_list = self.org_actions + [
            {"path": "/html/body/span/span[@class='select2-dropdown select2-dropdown--below']/span[2]/ul/li[3]"},
            {"path": ".//div[@id='actionsmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[2]/div/input"},
            {"path": ".//div[@id='actionsmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[2]/div/input",
                "extra_action": "clearinput"},
            {"path": ".//div[@id='actionsmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[2]/div/input"},
            {"path": ".//div[@id='actionsmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[2]/div/input",
                "extra_action": "setvalue", "value": "Organización Principal"},
            {"path": self.get_submit_button_path("actionsmodal")}
        ]
        self.create_gif_process(path_list, "change_org_name")

    def test_view_org_logs(self):
        path_list = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div[2]/ul/li[2]/a"}
        ]
        self.create_gif_process(path_list, "view_org_logs")

    def test_view_org_roles(self):
        path_list = self.view_org_roles + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[1]/div/a"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/a"}
        ]
        self.create_gif_process(path_list, "view_org_roles")

    def test_delete_org_role(self):
        path_list = self.view_org_roles + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[1]/div[2]/a"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/form/input[2]"}
        ]
        self.create_gif_process(path_list, "delete_org_role")

    def test_change_org_parent(self):
        path_list = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div[2]/ul/li[4]/span"},
            {"path": ".//div[@id='orgbyusermodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div/span/span/span"},
            {"path": ".//div[@id='orgbyusermodal']/span/span/span[2]/ul/li"},
            {"path": self.get_submit_button_path("orgbyusermodal")}
        ]
        self.create_gif_process(path_list, "change_org_parent")

    def test_delete_organization(self):
        path_list = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div[2]/ul/li[6]/a"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/form/input[2]"}
        ]
        self.create_gif_process(path_list, "delete_org")

    def test_add_organization_descendant(self):
        path_list = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div[2]/ul/li[5]/span"},
            {"path": ".//div[@id='addOrganizationmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div/div/input"},
            {"path": ".//div[@id='addOrganizationmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div/div/input",
                "extra_action": "setvalue", "value": "Organización Hija"},
            {"path": self.get_submit_button_path("addOrganizationmodal")}
        ]
        self.create_gif_process(path_list, "add_org_descendant")
