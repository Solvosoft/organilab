from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from organilab_test.tests.base import SeleniumBase


@tag('selenium')
class OrganizationSeleniumTest(SeleniumBase):
    fixtures = ["selenium/organization_manage.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.select_org_url = self.live_server_url + str(reverse('auth_and_perms:select_organization_by_user'))
        self.force_login(user=self.user, driver=self.selenium, base_url=self.live_server_url)
        self.folder_name = "create_org"
        self.create_directory_path(folder_name=self.folder_name)

    def test_create_organization(self):

        path_list = [
            {"path": ".//ul[@class='nav side-menu']/li[2]/a"},
            {"path": ".//ul[@class='nav side-menu']/li[2]/ul/li/a"},
            {"path": ".//span[@class='addOrgStructureEmpty']"},
            {"path": ".//div[@id='addOrganizationmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div/div/input[@id='id_name']"},
            {"path": ".//div[@id='addOrganizationmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div/div/input[@id='id_name']",
             "extra_action": "setvalue", "value": _("Organization Name")},
            {"path": ".//div[@id='addOrganizationmodal']/div/div[@class='modal-content']/form/div[@class='modal-footer']/button[@type='submit']"},
        ]

        self.create_gif_process(path_list, self.folder_name)
