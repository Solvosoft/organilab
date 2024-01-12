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
        path_list = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div[2]/ul/li[3]/a"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[1]/div/a"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/a"}
        ]
        self.create_gif_process(path_list, "view_org_roles")

    def test_change_org_parent(self):
        path_list = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div[2]/ul/li[4]/span"},
            {"path": ".//div[@id='orgbyusermodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div/span/span/span"},
            {"path": ".//div[@id='orgbyusermodal']/span/span/span[2]/ul/li"},
            {"path": self.get_submit_button_path("orgbyusermodal")}
        ]
        self.create_gif_process(path_list, "change_org_parent")


    def test_add_role_to_org(self):
        path_list = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div/div/div/h6"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div/div[2]/div/ul/li[1]/span"},
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[2]/div/div/input"},
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[2]/div/div/input",
             "extra_action": "setvalue", "value": "Administrar Laboratorio"},
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[2]/div/div[2]/div[1]/span"},
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div[2]/div/div[2]/div[2]/span/span/span"},
            {"path": ".//div[@id='addrolmodal']/span/span/span/ul/li"},
            {"path": ".//div[@id='addrolmodal']/div/div[@class='modal-content']/form/div[@class='modal-footer']/button[@id='saveroluserorg']"}
        ]
        self.create_gif_process(path_list, "add_role_to_org")


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
