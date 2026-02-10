from django.contrib.auth.models import User
from django.test import tag
from organilab_test.tests.base import SeleniumBase


class LaboratorySeleniumBase(SeleniumBase):
    fixtures = ["selenium/laboratory_selenium.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )
        self.path_base = [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div/div[1]/div/div/span/span[1]/span"
            },
            {"path": "/html/body/span/span/span/ul/li[1]"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div/div/div/a[1]"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div/div/div[1]/a"
            },
        ]


@tag("selenium")
class RegisterUserQRSeleniumTest(LaboratorySeleniumBase):
    def test_view_register_user_qr(self):

        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[2]/ul/li[4]/a"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div/h1",
                "screenshot_name": "registter_user_QR",
            },
        ]
        self.create_gif_process(path_list, "view_register_user_QR")

    def test_create_register_user_qr(self):

        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[2]/ul/li[4]/a"
            },
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div/a"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div/form/div/div/div[2]/div/span/span[1]/span"
            },
            {"path": "/html/body/span/span/span[2]/ul/li[2]"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div/form/div/div/div[3]/div/span/span[1]/span"
            },
            {"path": "/html/body/span/span/span[2]/ul/li[2]"},
            {"path": "//*[@id='id_code']", "extra_action": "clearInput"},
            {"path": "//*[@id='id_code']", "extra_action": "setvalue", "value": "A456"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div/form/div/div/div[5]/div/input"
            },
        ]
        self.create_gif_process(path_list, "create_register_user_QR")

    def test_update_register_user_qr(self):

        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[2]/ul/li[4]/a"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/table/tbody/tr/td[5]/a[1]"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div/form/div/div/div[2]/div/span/span[1]/span"
            },
            {"path": "/html/body/span/span/span[2]/ul/li[2]"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div/form/div/div/div[3]/div/span/span[1]/span"
            },
            {"path": "/html/body/span/span/span[2]/ul/li[2]"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div/form/div/div/div[5]/div/input"
            },
        ]
        self.create_gif_process(path_list, "update_register_user_QR")

    def test_delete_register_user_qr(self):

        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[2]/ul/li[4]/a"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/table/tbody/tr/td[5]/a[4]"
            },
            {"path": "/html/body/div[1]/div/div[3]/div/div/form/input[2]"},
        ]
        self.create_gif_process(path_list, "delete_register_user_QR")

    def test_downlooad_register_user_qr(self):

        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[2]/ul/li[4]/a"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/table/tbody/tr/td[5]/a[2]"
            },
        ]
        self.create_gif_process(path_list, "download_register_user_QR")

    def test_logentry_register_user_qr(self):

        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[2]/ul/li[4]/a"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/table/tbody/tr/td[5]/a[3]"
            },
        ]
        self.create_gif_process(path_list, "logentry_register_user_QR")
