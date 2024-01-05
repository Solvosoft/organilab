from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

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
        self.create_gif_process(path_list, "create_org")


    def test_delete_organization(self):
        path_list = [
            {"path": ".//ul[@class='nav side-menu']/li[2]/a"},
            {"path": ".//ul[@class='nav side-menu']/li[2]/ul/li/a"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div[2]/ul/li[6]/a"}
        ]
        self.create_gif_process(path_list, "delete_org")
