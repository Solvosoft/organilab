from django.contrib.auth.models import User
from django.urls import reverse

from organilab_test.tests.base import SeleniumBase


class ManageOrganizationsSeleniumTest(SeleniumBase):
    fixtures = ["selenium/organization_manage.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.select_org_url = self.live_server_url + str(reverse('auth_and_perms:select_organization_by_user'))
        self.force_login(user=self.user, driver=self.selenium, base_url=self.live_server_url)

        self.path_base = [
            {"path": ".//ul[@class='nav side-menu']/li[2]/a"},
            {"path": ".//ul[@class='nav side-menu']/li[2]/ul/li/a"}
        ]

        self.select_organization = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[2]/div/div/div[1]/div[1]/div[2]/div/ins"}
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


