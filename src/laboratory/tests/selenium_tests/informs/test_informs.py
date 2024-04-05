from django.contrib.auth.models import User
from django.test import tag
from djgentelella.models import MenuItem

from organilab_test.tests.base import SeleniumBase

class InformSeleniumBase(SeleniumBase):
    fixtures = ["selenium/laboratory_selenium.json"]
    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(user=self.user, driver=self.selenium, base_url=self.live_server_url)
        print(MenuItem.objects.values('icon'))
        self.path_base = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[1]/div/div/span/span[1]/span"},
            {"path": "/html/body/span/span/span/ul/li[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div/div/div/a[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div/div/div[1]/a"},
            {"path": "/html/body/div[1]/div/div[2]/nav/div[1]/ul[2]/li[5]/a"},
        ]


@tag('selenium')
class InformSeleniumTest(InformSeleniumBase):

    def test_view_inform(self):

        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div/div/h3/span", "screenshot_name": "view_informs"},
        ]
        self.create_gif_process(path_list, "view_inform")
    def test_add_inform(self):

        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div/div/div/div[1]/a"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div/div[2]/form/div[1]/div/input", "extra_action":"setvalue", "value":"Prime Informe"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div/div[2]/form/div[2]/div/span/span[1]/span/span[1]"},
            {"path": "/html/body/span/span/span[2]/ul/li[3]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div/div[2]/form/div[3]/button[2]"},
        ]
        self.create_gif_process(path_list, "add_inform")
    def test_review_inform(self):
        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div/div/div/div[2]/div/div[2]/div/table/tbody/tr/td[5]/a[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div[1]/form/div/div/div[1]/div[1]/div[1]/input","extra_action":"clearinput"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div[1]/form/div/div/div[1]/div[1]/div[1]/input","extra_action":"setvalue","value":"Primer Laboratorio"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div[1]/form/div/div/div[1]/div[2]/div[1]/textarea", "extra_action":"clearinput"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div[1]/form/div/div/div[1]/div[2]/div[1]/textarea","extra_action":"setvalue","value":"Caída de estante de reactivos"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div[1]/form/button"},
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
        ]
        self.create_gif_process(path_list, "review_inform")
        self.finalize_inform()
    def test_remove_inform(self):
        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div/div/div/div[2]/div/div[2]/div/table/tbody/tr/td[5]/a[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div/div/h3/span"},
        ]
        self.create_gif_process(path_list, "remove_inform")

    def test_crud_inform_observation(self):
        path_list = self.path_base+[

            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div/div/div/div[2]/div/div[2]/div/table/tbody/tr/td[5]/a[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/button"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div[2]/div/div/div/div[1]/button"},
            {"path": "/html/body/div[3]/div/div[2]/textarea", "extra_action": "setvalue", "value": "Primer comentario"},
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/div/div/div[4]"},
        ]
        self.create_gif_process(path_list, "add_inform_observation")
        self.edit_inform_observation()
        self.remove_inform_observation()

    def edit_inform_observation(self):
        path_list = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/div/div/div[2]/div[1]/i[1]"},
            {"path": "/html/body/div[3]/div/div[2]/textarea", "extra_action": "clearinput"},
            {"path": "/html/body/div[3]/div/div[2]/textarea", "extra_action": "setvalue", "value": "Comentario Actualizado."},
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/div/div/div[4]"},
        ]
        self.create_gif_process(path_list, "edit_inform_observation")

    def remove_inform_observation(self):
        path_list = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/div/div/div[2]/div[1]/i[2]"},
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},

        ]
        self.create_gif_process(path_list, "remove_inform_observation")

    def finalize_inform(self):
        path_list =[
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div/div/div/div[2]/div/div[2]/div/table/tbody/tr/td[5]/a[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div[1]/form/button"},
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},

        ]
        self.create_gif_process(path_list, "finalize_inform")

