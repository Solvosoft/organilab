from django.test import tag

from laboratory.tests.selenium_tests.manage_organizations.base import ManageOrganizationsSeleniumTest


@tag('selenium')
class ButtonBoxCollapseOrgNameTest(ManageOrganizationsSeleniumTest):

    def setUp(self):
        super().setUp()

        self.role_button_box = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div/div/div/h6"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div/div[2]/div/ul/li[1]/span"}
        ]

    def test_add_role_to_org_without_copy_permissions_from_others_roles(self):
        path_list = self.role_button_box + [
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[2]/div/div/input"},
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[2]/div/div/input",
                "extra_action": "setvalue", "value": "Gestión de objetos"},
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-footer']/button[@id='saveroluserorg']"}
        ]
        self.create_gif_process(path_list,
                                "add_role_to_org_without_copy_permissions_from_others_roles")

    def test_add_role_to_org_copy_permissions_from_others_roles(self):
        path_list = self.role_button_box + [
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[2]/div/div/input"},
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[2]/div/div/input",
                "extra_action": "setvalue", "value": "Administrar Laboratorio"},
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[2]/div/div[2]/div[1]/span"},
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[2]/div/div[2]/div[2]/span/span/span"},
            {"path": ".//div[@id='addrolmodal']/span/span/span/ul/li"},
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-footer']/button[@id='saveroluserorg']"}
        ]
        self.create_gif_process(path_list,
                                "add_role_to_org_copy_permissions_from_others_roles")

    def test_copy_role_to_org(self):
        path_list = self.role_button_box + [
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[1]/div/button[2]"},
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[2]/div[2]/div/div[2]/span/span/span"},
            {"path": ".//div[@id='addrolmodal']/span/span/span/ul/li[2]"},
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-footer']/button[@id='saveroluserorg']"}
        ]
        self.create_gif_process(path_list, "copy_role_to_org")

    def test_add_user_to_org_from_button_box(self):
        path_list = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div/div/div/h6"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div/div[2]/div/ul/li[2]/a"},
            {"path": ".//form/div[1]/div/input"},
            {"path": ".//form/div[1]/div/input", "extra_action": "setvalue",
             "value": "Andrea"},
            {"path": ".//form/div[2]/div/input"},
            {"path": ".//form/div[2]/div/input", "extra_action": "setvalue",
             "value": "Rojas Barrantes"},
            {"path": ".//form/div[3]/div/input"},
            {"path": ".//form/div[3]/div/input", "extra_action": "setvalue",
             "value": "andrearb@"},
            {"path": ".//form/div[3]/div/input", "extra_action": "move_cursor_end",
             "reduce_length": 3},
            {"path": ".//form/div[3]/div/input", "extra_action": "setvalue",
             "value": "gmail.com"},
            {"path": ".//form/div[4]/div/input"},
            {"path": ".//form/div[4]/div/input", "extra_action": "setvalue",
             "value": "50688888888"},
            {"path": ".//form/div[5]/div/input"},
            {"path": ".//form/div[5]/div/input", "extra_action": "setvalue",
             "value": "707770777"},
            {"path": ".//form/div[6]/div/input"},
            {"path": ".//form/div[6]/div/input", "extra_action": "setvalue",
             "value": "Estudiante"},
            {"path": ".//form/div[8]/input"}
        ]
        self.create_gif_process(path_list, "add_user_to_org_from_button_box")

    def test_relate_user_to_org_from_button_box(self):
        path_list = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div/div/div/h6"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div/div[2]/div/ul/li[3]/a"},
            {"path": "//*[@id='modaluser1']/div/form/div/div[@class='modal-body']/span/span/span"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div[1]/div[2]/div/div/div[2]/ul/div/div[2]/span/span/span/ul/li[2]"},
            {"path": "//*[@id='modaluser1']/div/form/div/div[@class='modal-footer']/button[@type='submit']"}
        ]
        self.create_gif_process(path_list, "relate_user_to_org_from_button_box")

    def test_add_laboratory_to_org(self):
        path_list = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div/div/div/h6"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div/div[2]/div/ul/li[4]/a"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[2]/form/div/div[1]/div/input"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[2]/form/div/div[1]/div/input",
                "extra_action": "setvalue", "value": "Laboratorio Estudiantil"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[2]/form/div/div[2]/div/input"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[2]/form/div/div[2]/div/input",
                "extra_action": "setvalue", "value": "(506)2222-2222"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[2]/form/div/div[3]/div/input"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[2]/form/div/div[3]/div/input",
                "extra_action": "setvalue", "value": "San Pedro, San José"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[2]/form/button[@type='submit']",
                "scroll": "window.scrollTo(0, 300)"},

        ]
        self.create_gif_process(path_list, "add_laboratory_to_org")

    def test_relate_external_laboratory_to_org(self):
        path_list = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[4]/div/div/div/div/div/h6"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[4]/div/div/div/div[2]/div/ul/li[5]/a"},
            {"path": ".//div[@id='relOrganizationmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/p/span/span/span"},
            {"path": "/html/body/span/span[@class='select2-dropdown select2-dropdown--below']/span/ul/li[1]"},
            {"path": self.get_submit_button_path("relOrganizationmodal")}
        ]
        self.create_gif_process(path_list, "relate_external_laboratory_to_org")

    def test_relate_org_base_laboratory_to_org_child(self):
        path_list = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[5]/div/div/div/div/div/h6"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[5]/div/div/div/div[2]/div/ul/li[5]/a"},
            {"path": ".//div[@id='relOrganizationmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/p/span/span/span"},
            {"path": "/html/body/span/span[@class='select2-dropdown select2-dropdown--below']/span/ul/li[1]"},
            {"path": self.get_submit_button_path("relOrganizationmodal")}
        ]
        self.create_gif_process(path_list, "relate_org_base_laboratory_to_org_child")
