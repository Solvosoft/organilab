from django.contrib.auth.models import User
from django.urls import reverse
from organilab_test.tests.base import SeleniumBase
from django.test import tag
from django.contrib.auth.models import User
from django.test import tag
from organilab_test.tests.base import SeleniumBase

@tag('selenium')
class MyProcedureSeleniumTest(SeleniumBase):
    fixtures = ["selenium/laboratory_selenium.json"]
    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(user=self.user, driver=self.selenium, base_url=self.live_server_url)
        self.path_base = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[1]/div/div/span/span[1]/span"},
            {"path": "/html/body/span/span/span/ul/li[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div/div/div/a[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div/div/div[1]/a"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[2]/ul/li[2]/a"},
        ]
    def test_view_my_procedure(self):
        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div[1]/div/div/div/h1/span", "screenshot_name": "view_my_procedure"},
            ]
        self.create_gif_process(path_list, "view_my_procedure")

    def test_add_my_procedure(self):
        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div[1]/div/div/div/div/div[1]/div[2]/div/button"},
            {"path": "//*[@id='id_name']", "extra_action": "clearinput"},
            {"path": "//*[@id='id_name']", "extra_action": "setvalue", "value":"Primer Procedimiento"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div[2]/div/div/div[2]/form/div[2]/div/span/span[1]/span"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div[2]/span/span/span[2]/ul/li[1]"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div[2]/div/div/div[2]/form/div[3]/button[2]"},
            ]
        self.create_gif_process(path_list, "add_my_procedure")

    def test_delete_myprocedure(self):
        path_list = self.path_base+[

            {"path": "/html/body/div[1]/div[1]/div[3]/div/div[1]/div/div/div/div/div[2]/table/tbody/tr[1]/td[5]/a[3]"},
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
            ]
        self.create_gif_process(path_list, "delete_myprocedure")

    def test_myprocedure_reservation(self):
        set_initial_date="""document.querySelector('#id_initial_date').value='02/05/2024 14:36 PM'"""
        set_final_date="""document.querySelector('#id_final_date').value='02/06/2024 01:00 AM'"""
        path_list = self.path_base+[

            {"path": "/html/body/div[1]/div[1]/div[3]/div/div[1]/div/div/div/div/div[2]/table/tbody/tr[1]/td[5]/a[2]"},
            {"path": "//*[@id='id_initial_date']"},
            {"path": "//*[@id='id_initial_date']", "extra_action": "clearinput"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div[3]/div/div/div[2]/form/div[1]/div/span",
             "extra_action": "script", "value": set_initial_date},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div[3]/div/div/div[2]/div"},
            {"path": "//*[@id='id_final_date']"},
            {"path": "//*[@id='id_final_date']", "extra_action": "clearinput"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div[3]/div/div/div[2]/form/div[2]/div/span/i", "extra_action": "script", "value": set_final_date},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div[3]/div/div/div[2]/div"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div[3]/div/div/div[3]/button[2]"},
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
            {"path": "/html/body/div[1]/div[1]/div[2]/nav/div[1]/ul[2]/li[3]/a"},
            ]
        self.create_gif_process(path_list, "myprocedure_reservation")

    def test_add_observation_my_procedure(self):
        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div[1]/div/div/div/div/div[2]/table/tbody/tr[1]/td[5]/a[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div[2]/div[1]/form/div/div[1]/div/div[2]/input"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div[2]/div[2]/div/div[1]/div[3]/div/button"},
            {"path": "//*[@id='id_comment']", "extra_action": "clearinput"},
            {"path": "//*[@id='id_comment']", "extra_action": "setvalue", "value":"Se ve excelente el procedimiento"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div/div[3]/button[2]"},
            ]
        self.create_gif_process(path_list, "add_my_procedure_observation")

    def test_update_observation_my_procedure(self):
        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div[1]/div/div/div/div/div[2]/table/tbody/tr[1]/td[5]/a[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div[2]/div[1]/form/div/div[1]/div/div[2]/input"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div[2]/div[2]/div/div[2]/div/table/tbody/tr/td[4]/div[1]/i[1]",
             "scroll": "window.scrollTo(0, 0)"},
            {"path": "/html/body/div[4]/div/div[2]/textarea", "extra_action": "clearinput"},
            {"path": "/html/body/div[4]/div/div[2]/textarea", "extra_action": "setvalue",
             "value": "Revisar de nuevo la lista de objectos"},
            {"path": "/html/body/div[4]/div/div[3]/button[1]"},
            {"path": "/html/body/div[4]/div/div[3]/button[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div[2]/div[2]/div/div[2]/div/table/tbody/tr/td[3]"}
            ]
        self.create_gif_process(path_list, "update_my_procedure_observation")

    def test_delete_observation_my_procedure(self):
        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div[1]/div/div/div/div/div[2]/table/tbody/tr[1]/td[5]/a[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div[2]/div[1]/form/div/div[1]/div/div[2]/input"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div[2]/div[2]/div/div[2]/div/table/tbody/tr/td[4]/div[1]/i[2]",
             "scroll": "window.scrollTo(0, 0)"},
            {"path": "/html/body/div[4]/div/div[3]/button[1]"},
            {"path": "/html/body/div[4]/div/div[3]/button[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div[2]/div[2]/div/div[2]/div/table/thead/tr[2]/th[1]/input"}
            ]
        self.create_gif_process(path_list, "delete_my_procedure_observation")

    def finalize_myprocedure(self):
        path_list = [
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div[1]/div/div/div/div/div[2]/table/tbody/tr[1]/td[5]/a[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div[2]/div[1]/form/button",
             "scroll": "window.scrollTo(0, document.body.scrollHeight)"},
            {"path": "/html/body/div[4]/div/div[3]/button[1]"},
            ]
        self.create_gif_process(path_list, "finalize_my_procedure")

    def test_review_myprocedure(self):
        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div[1]/div/div/div/div/div[2]/table/tbody/tr[1]/td[5]/a[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div[2]/div[1]/form/button",
             "scroll": "window.scrollTo(0, document.body.scrollHeight)"},
            {"path": "/html/body/div[4]/div/div[3]/button[1]"},
            ]
        self.create_gif_process(path_list, "review_my_procedure")
        self.finalize_myprocedure()

