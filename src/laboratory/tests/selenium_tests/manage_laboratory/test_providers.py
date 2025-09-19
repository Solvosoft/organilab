from django.contrib.auth.models import User
from django.test import tag
from organilab_test.tests.base import SeleniumBase


@tag("selenium")
class ProviderSeleniumTest(SeleniumBase):
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
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[4]/a"},
        ]

    def test_view_providers(self):
        path_list = self.path_base + [
            {
                "path": ".//div[1]/div/div[3]/div/div/div[1]/h1",
                "screenshot_name": "view_provider",
            },
        ]
        self.create_gif_process(path_list, "view_providers")

    def test_add_provider(self):
        path_list = self.path_base + [
            {"path": "/html/body/div[1]/div/div[3]/div/div/a"},
            {"path": "//*[@id='id_name']", "extra_action": "clearinput"},
            {
                "path": "//*[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Fanal",
            },
            {"path": "//*[@id='id_phone_number']", "extra_action": "clearinput"},
            {
                "path": "//*[@id='id_phone_number']",
                "extra_action": "setvalue",
                "value": "(506)2234-0000",
            },
            {"path": "//*[@id='id_email']", "extra_action": "clearinput"},
            {"path": "//*[@id='id_email']", "extra_action": "setvalue", "value": "kcb"},
            {
                "path": "//*[@id='id_email']",
                "extra_action": "move_cursor_end",
                "reduce_length": 3,
            },
            {
                "path": "//*[@id='id_email']",
                "extra_action": "setvalue",
                "value": "@gmail.com",
            },
            {"path": "//*[@id='id_legal_identity']", "extra_action": "clearinput"},
            {
                "path": "//*[@id='id_legal_identity']",
                "extra_action": "setvalue",
                "value": "123456879",
            },
        ]
        self.create_gif_process(path_list, "add_provider")

    def test_update_provider(self):
        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/table/tbody/tr/td[4]/a"
            },
            {"path": "//*[@id='id_phone_number']", "extra_action": "clearinput"},
            {
                "path": "//*[@id='id_phone_number']",
                "extra_action": "setvalue",
                "value": "(506)2234-0000",
            },
            {"path": "//*[@id='id_legal_identity']", "extra_action": "clearinput"},
            {
                "path": "//*[@id='id_legal_identity']",
                "extra_action": "setvalue",
                "value": "123456879",
            },
        ]
        self.create_gif_process(path_list, "update_provider")
