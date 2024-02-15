from django.contrib.auth.models import User
from django.test import tag
from organilab_test.tests.base import SeleniumBase

class RiskSeleniumBase(SeleniumBase):
    fixtures = ["selenium/risk_management.json"]
    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(user=self.user, driver=self.selenium, base_url=self.live_server_url)
        self.path_base = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[1]/div/div/span/span[1]/span"},
            {"path": "/html/body/span/span/span/ul/li[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div/div/div/a[3]"},
        ]


@tag('selenium')
class RiskSeleniumTest(RiskSeleniumBase):

    def test_view_risk(self):

        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div/h3/span", "screenshot_name": "view_risk_module"},
        ]
        self.create_gif_process(path_list, "view_risk")

    def test_add_riak(self):

        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/form/div[2]/div/a"},
            {"path": "//*[@id='id_name']", "extra_action":"clearinput"},
            {"path": "//*[@id='id_name']", "extra_action":"setvalue", "value":"Bodega de equipos"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[2]/div/span"},
            {"path": "/html/body/span/span/span/ul/li[1]"},
            {"path": "//*[@id='id_num_workers']", "extra_action":"clearinput"},
            {"path": "//*[@id='id_num_workers']", "extra_action":"setvalue", "value":5},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[4]/div/div/span"},
            {"path": "/html/body/span/span/span[2]/ul/li[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[5]/div/button"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div/h3/span"},
        ]
        self.create_gif_process(path_list, "add_risk")


    def test_edit_risk(self):

        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div/ul/li[1]/div/div[2]/div/a[1]"},
            {"path": "//*[@id='id_name']", "extra_action":"clearinput"},
            {"path": "//*[@id='id_name']", "extra_action":"setvalue", "value":"Bodega de equipos"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[5]/div/button"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div/h3/span"},
        ]
        self.create_gif_process(path_list, "edit_risk")
    def test_add_zone_type(self):

        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/form/div[2]/div/a"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[4]/div/div/button"},
            {"path": "/html/body/div[3]/div/div/div[2]/div/form/div[1]/div/input", "extra_action": "clearinput"},
            {"path": "/html/body/div[3]/div/div/div[2]/div/form/div[1]/div/input", "extra_action": "setvalue", "value":"Estanteria"},
            {"path": "/html/body/div[3]/div/div/div[2]/div/form/div[2]/div/select/option[1]"},
            {"path": "/html/body/div[3]/div/div/div[3]/button[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[4]/div/div/span"},
        ]
        self.create_gif_process(path_list, "add_zone_type")
