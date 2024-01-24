from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse

from laboratory.models import OrganizationStructure
from organilab_test.tests.base import SeleniumBase


@tag('selenium')
class OrganizationSeleniumTest(SeleniumBase):
    fixtures = ["selenium/organization_manage.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.org = OrganizationStructure.objects.get(pk=1)
        self.select_org_url = self.live_server_url + str(reverse('auth_and_perms:select_organization_by_user'))
        self.force_login(user=self.user, driver=self.selenium, base_url=self.live_server_url)
        self.path_base = [
            {"path": ".//ul[@class='nav side-menu']/li[2]/a"},
            {"path": ".//ul[@class='nav side-menu']/li[2]/ul/li/a"}
        ]
        self.org_actions = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div[2]/ul/li[1]"},
            {"path": ".//div[@id='actionsmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div/div/span/span/span"}
        ]

        self.role_button_box = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div/div/div/h6"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div/div[2]/div/ul/li[1]/span"}
        ]

        self.view_org_roles = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div[2]/ul/li[3]/a"}
        ]

        self.select_organization = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div[1]/div[1]/div[2]/div/ins"}
        ]

        self.tab_lab = self.select_organization + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/ul/li[1]/a"}
        ]

        self.tab_org = self.select_organization + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/ul/li[2]/a"}
        ]

        self.select_laboratory_tab_lab = self.tab_lab + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/div/div[@id='bylabs']/div/div/div/span/span/span"},
            {"path": "/html/body/span/span[@class='select2-dropdown select2-dropdown--below']/span/ul/li[1]"},
            {"path": ".//span[contains(@class,'applyasrole')]"}
        ]

        self.button_save_permission_rol = [{"path": "//*[@id='modal1']/div/form/div/div[3]/button[2]"}]

        self.add_permission_rol = [
            {"path": ".//div[@id='modal1']/div/form/div/div[@class='modal-body']/span/span/span"},
            {"path": ".//div[@id='modal1']/span/span/span/ul/li"}
        ] + self.button_save_permission_rol

        self.remove_and_save_permission_rol = [
            {"path": ".//div[@id='modal1']/div/form/div/div[@class='modal-body']/div/input[2]"}
        ] + self.button_save_permission_rol

        self.use_and_save_permission_rol = [
            {"path": ".//div[@id='modal1']/div/form/div/div[@class='modal-body']/div/input[3]"}
        ] + self.button_save_permission_rol

    def get_submit_button_path(self, id_modal, button_type="submit"):
        return ".//div[@id='%s']/div/div[@class='modal-content']/form/div[@class='modal-footer']/button[@type='%s']" % (id_modal, button_type)

    def test_create_organization(self):
        path_list = self.path_base + [
            {"path": ".//span[@class='addOrgStructureEmpty']"},
            {"path": ".//div[@id='addOrganizationmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div/div/input[@id='id_name']"},
            {"path": ".//div[@id='addOrganizationmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div/div/input[@id='id_name']",
             "extra_action": "setvalue", "value": "Sede Central"},
            {"path": self.get_submit_button_path("addOrganizationmodal")}
        ]
        self.create_gif_process(path_list, "create_org")

    def test_delete_organization(self):
        path_list = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div[2]/ul/li[6]/a"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/form/input[2]"}
        ]
        self.create_gif_process(path_list, "delete_org")

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

    def test_add_organization_descendant(self):
        path_list = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div[2]/ul/li[5]/span"},
            {"path": ".//div[@id='addOrganizationmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div/div/input"},
            {"path": ".//div[@id='addOrganizationmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div/div/input",
                "extra_action": "setvalue", "value": "Organización Hija"},
            {"path": self.get_submit_button_path("addOrganizationmodal")}
        ]
        self.create_gif_process(path_list, "add_org_descendant")

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

    def test_add_role_to_org_without_copy_permissions_from_others_roles(self):
        path_list = self.role_button_box + [
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[2]/div/div/input"},
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[2]/div/div/input",
             "extra_action": "setvalue", "value": "Gestión de objetos"},
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-footer']/button[@id='saveroluserorg']"}
        ]
        self.create_gif_process(path_list, "add_role_to_org_without_copy_permissions_from_others_roles")

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
        self.create_gif_process(path_list, "add_role_to_org_copy_permissions_from_others_roles")

    def test_copy_role_to_org(self):
        path_list = self.role_button_box + [
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[1]/div/button[2]"},
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[2]/div[2]/div/div[2]/span/span/span"},
            {"path": ".//div[@id='addrolmodal']/span/span/span/ul/li[2]"},
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-footer']/button[@id='saveroluserorg']"}
        ]
        self.create_gif_process(path_list,"copy_role_to_org")

    def test_change_profile_permission_group_by_org(self):
        path_list = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[3]/div/div/div[1]/div[1]/div[2]/div/ins"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/ul/li[3]/a"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/div/div[@id='byprofile']/form/div/div/span/span/span"},
            {"path": "/html/body/span/span[@class='select2-dropdown select2-dropdown--below']/span[2]/ul/li[2]"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/div/div[@id='byprofile']/form/div[2]/div/span/span/span"},
            {"path": "/html/body/span/span[@class='select2-dropdown select2-dropdown--below']/span/ul/li[3]"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/div/div[@id='byprofile']/form/button[@id='savegroupsbyprofile']"},
        ]
        self.create_gif_process(path_list, "change_profile_permission_group_by_org")

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
        self.create_gif_process(path_list,"relate_external_laboratory_to_org")

    def test_relate_org_base_laboratory_to_org_child(self):
        path_list = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[5]/div/div/div/div/div/h6"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[5]/div/div/div/div[2]/div/ul/li[5]/a"},
            {"path": ".//div[@id='relOrganizationmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/p/span/span/span"},
            {"path": "/html/body/span/span[@class='select2-dropdown select2-dropdown--below']/span/ul/li[1]"},
            {"path": self.get_submit_button_path("relOrganizationmodal")}
        ]
        self.create_gif_process(path_list,"relate_org_base_laboratory_to_org_child")

    def test_add_user_to_org_from_button_box(self):
        path_list = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div/div/div/h6"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div/div[2]/div/ul/li[2]/a"},
            {"path": ".//form/div[1]/div/input"},
            {"path": ".//form/div[1]/div/input", "extra_action": "setvalue", "value": "Andrea"},
            {"path": ".//form/div[2]/div/input"},
            {"path": ".//form/div[2]/div/input", "extra_action": "setvalue", "value": "Rojas Barrantes"},
            {"path": ".//form/div[3]/div/input"},
            {"path": ".//form/div[3]/div/input", "extra_action": "setvalue", "value": "andrearb@gmail.com"},
            {"path": ".//form/div[4]/div/input"},
            {"path": ".//form/div[4]/div/input", "extra_action": "setvalue", "value": "50688888888"},
            {"path": ".//form/div[5]/div/input"},
            {"path": ".//form/div[5]/div/input", "extra_action": "setvalue", "value": "707770777"},
            {"path": ".//form/div[6]/div/input"},
            {"path": ".//form/div[6]/div/input", "extra_action": "setvalue", "value": "Estudiante"},
            {"path": ".//form/div[7]/input"}
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

    def test_relate_user_to_org_and_lab_from_tab_org(self):
        path_list = self.tab_org + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/div/div[@id='byorgs']/div/button"},
            {"path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/ul/li[2]/button"},
            {"path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/div/div[2]/div[1]/form/div/div/div/input"},
            {"path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/div/div[2]/div[1]/form/div/div/div/input",
             "extra_action": "setvalue", "value": "ricardom@gmail.com"},
            {"path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/div/div[2]/div[2]/button[@id='relemailbtn']"},
            {"path": "/html/body/div[4]/div/div[3]/button[1]"},
            {"path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/ul/li[1]/button"},
            {"path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/div/div/form/div/div[1]/div/span/span/span[1]"},
            {"path": ".//div[@id='relprofilelabmodal']/span/span/span[2]/ul/li"},
            {"path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/div/div/form/div/div[2]/div/span/span/span[1]"},
            {"path": ".//div[@id='relprofilelabmodal']/span/span/span/ul/li"},
            {"path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/div/div/form/div[2]/button[@id='relprofilewithlaboratorybtn']"}
        ]
        self.create_gif_process(path_list, "relate_user_to_org_and_lab_from_tab_org")

    def test_relate_user_to_org_and_lab_from_tab_lab(self):
        path_list = self.tab_lab + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/div/div[@id='bylabs']/div/div/div/span/span/span"},
            {"path": "/html/body/span/span[@class='select2-dropdown select2-dropdown--below']/span/ul/li[1]"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/div/div[@id='bylabs']/div[2]/button"},
            {"path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/ul/li[2]/button"},
            {"path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/div/div[2]/div[1]/form/div/div/div/input"},
            {"path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/div/div[2]/div[1]/form/div/div/div/input",
            "extra_action": "setvalue", "value": "ricardom@gmail.com"},
            {"path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/div/div[2]/div[2]/button[@id='relemailbtn']"},
            {"path": "/html/body/div[4]/div/div[3]/button[1]"},
            {"path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/ul/li[1]/button"},
            {"path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/div/div/form/div/div[1]/div/span/span/span[1]"},
            {"path": ".//div[@id='relprofilelabmodal']/span/span/span[2]/ul/li"},
            {"path": ".//div[@id='relprofilelabmodal']/div/div/div[@class='modal-body']/div/div/form/div[2]/button[@id='relprofilewithlaboratorybtn']"}
        ]
        self.create_gif_process(path_list, "relate_user_to_org_and_lab_from_tab_lab")

    def test_add_permission_rol_to_user_from_tab_lab(self):
        path_list = self.select_laboratory_tab_lab + self.add_permission_rol
        self.create_gif_process(path_list, "add_permission_rol_to_user_from_tab_lab")

    def test_remove_permission_rol_to_user_from_tab_lab(self):
        path_list = self.select_laboratory_tab_lab + self.remove_and_save_permission_rol
        self.create_gif_process(path_list, "remove_permission_rol_to_user_from_tab_lab")

    def test_use_selected_permission_rol_to_user_from_tab_lab(self):
        path_list = self.select_laboratory_tab_lab + [
            {"path": ".//div[@id='modal1']/div/form/div/div[@class='modal-body']/span/span/span/ul/li/button"},
            {"path": ".//div[@id='modal1']/span/span/span/ul/li[2]"}
        ] + self.use_and_save_permission_rol
        self.create_gif_process(path_list, "use_selected_permission_rol_to_user_from_tab_lab")

    def test_add_permission_rol_to_user_from_tab_org(self):
        path_list = self.tab_org + [
            {"path": ".//span[contains(@class,'applyasrole')]"},
        ] + self.add_permission_rol
        self.create_gif_process(path_list, "add_permission_rol_to_user_from_tab_org")

    def test_remove_permission_rol_to_user_from_tab_org(self):
        path_list = self.tab_org + [
            {"path": ".//span[contains(@class,'applyasrole')]"}
        ] + self.remove_and_save_permission_rol
        self.create_gif_process(path_list, "remove_permission_rol_to_user_from_tab_org")


    def test_use_selected_permission_rol_to_user_from_tab_org(self):
        path_list = self.tab_org + [
            {"path": ".//span[contains(@class,'applyasrole')]"},
            {"path": ".//div[@id='modal1']/div/form/div/div[@class='modal-body']/span/span/span/ul/li/button"},
            {"path": ".//div[@id='modal1']/span/span/span/ul/li[2]"}
        ] + self.use_and_save_permission_rol
        self.create_gif_process(path_list, "use_selected_permission_rol_to_user_from_tab_org")
