from django.test import tag
from laboratory.tests.selenium_tests.manage_organizations.base import (
    ManageOrganizationsSeleniumTest,
)


@tag("selenium")
class LaboratoryTabTest(ManageOrganizationsSeleniumTest):

    def setUp(self):
        super().setUp()

        self.tab_lab = self.select_organization + [
            {
                "path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/ul/li[1]/a"
            }
        ]

        self.select_laboratory_tab_lab = self.tab_lab + [
            {
                "path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/div/div[@id='bylabs']/div/div/div/span/span/span"
            },
            {
                "path": "/html/body/span/span[@class='select2-dropdown select2-dropdown--below']/span/ul/li[1]"
            },
        ]

    def test_relate_user_to_org_and_lab_from_tab_lab(self):
        path_list = self.tab_lab + [
            {
                "path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/div/div[@id='bylabs']/div/div/div/span/span/span"
            },
            {
                "path": "/html/body/span/span[@class='select2-dropdown select2-dropdown--below']/span/ul/li[1]"
            },
            {
                "path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/div/div[@id='bylabs']/div[2]/button"
            },
            {
                "path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/ul/li[2]/button"
            },
            {
                "path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/div/div[2]/div[1]/form/div/div/div/input"
            },
            {
                "path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/div/div[2]/div[1]/form/div/div/div/input",
                "extra_action": "setvalue",
                "value": "ricardom@gmail.com",
            },
            {
                "path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/div/div[2]/div[2]/button[@id='relemailbtn']"
            },
            {"path": "/html/body/div[4]/div/div[3]/button[1]"},
            {
                "path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/ul/li[1]/button"
            },
            {
                "path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/div/div/form/div/div[1]/div/span/span/span[1]"
            },
            {"path": ".//div[@id='relprofilelabmodal']/span/span/span[2]/ul/li"},
            {
                "path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/div/div/form/div[2]/button[@id='relprofilewithlaboratorybtn']"
            },
        ]
        self.create_gif_process(path_list, "relate_user_to_org_and_lab_from_tab_lab")

    def test_add_permission_rol_to_user_from_tab_lab(self):
        path_list = (
            self.select_laboratory_tab_lab
            + [{"path": ".//span[contains(@class,'applyasrole')]"}]
            + self.add_permission_rol
        )
        self.create_gif_process(path_list, "add_permission_rol_to_user_from_tab_lab")

    def test_remove_permission_rol_to_user_from_tab_lab(self):
        path_list = (
            self.select_laboratory_tab_lab
            + [{"path": ".//span[contains(@class,'applyasrole')]"}]
            + self.remove_and_save_permission_rol
        )
        self.create_gif_process(path_list, "remove_permission_rol_to_user_from_tab_lab")

    def test_use_selected_permission_rol_to_user_from_tab_lab(self):
        path_list = (
            self.select_laboratory_tab_lab
            + [
                {"path": ".//span[contains(@class,'applyasrole')]"},
                {
                    "path": ".//div[@id='modal1']/div/form/div/div[@class='modal-body']/span/span/span/ul/li/button"
                },
                {"path": ".//div[@id='modal1']/span/span/span/ul/li[2]"},
            ]
            + self.use_and_save_permission_rol
        )
        self.create_gif_process(
            path_list, "use_selected_permission_rol_to_user_from_tab_lab"
        )

    def test_delete_relation_user_lab_from_tab_lab(self):
        path_list = self.select_laboratory_tab_lab + [
            {"path": ".//table/tbody/tr[2]/td[1]", "scroll": "window.scrollTo(0, 250)"},
            {"path": ".//table/tbody/tr[3]/td/ul/li/span[2]/i"},
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
        ]
        self.create_gif_process(path_list, "delete_relation_user_lab_from_tab_lab")

    def test_delete_relation_user_lab_and_deactivate_user_from_tab_lab(self):
        path_list = self.select_laboratory_tab_lab + [
            {"path": ".//table/tbody/tr[2]/td[1]", "scroll": "window.scrollTo(0, 250)"},
            {"path": ".//table/tbody/tr[3]/td/ul/li/span[2]/i"},
            {"path": "//*[@id='swal2-checkbox']"},
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
        ]
        self.create_gif_process(
            path_list, "delete_relation_user_lab_and_deactivate_user_from_tab_lab"
        )
