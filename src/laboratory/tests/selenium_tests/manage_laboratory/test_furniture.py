from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse
from laboratory.models import OrganizationStructure
from organilab_test.tests.base import SeleniumBase


@tag('selenium')
class FurnitureSeleniumTest(SeleniumBase):
    fixtures = ["selenium/laboratory_selenium.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.org = OrganizationStructure.objects.get(pk=1)
        self.select_org_url = self.live_server_url + str(reverse('auth_and_perms:select_organization_by_user'))
        self.force_login(user=self.user, driver=self.selenium, base_url=self.live_server_url)

    def test_create_furniture(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[1]/a"},
            {"path":".//div[1]/div/div[3]/div/div/div[2]/div[1]/div/ul/li/div/div[1]/div/div[3]/div/button[2]"},
            {"path":".//*[@id='furnitureModal']/div/div/form/div[2]/div[1]/div/input", "extra_action": "clearinput"},
            {"path":".//*[@id='furnitureModal']/div/div/form/div[2]/div[1]/div/input", "extra_action": "setvalue","value":"Generico"},
            {"path":".//div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/form/div[2]/div[2]/div/span"},
            {"path": ".//span/span/span[2]/ul/li[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/form/div[3]/button[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/form/div[1]/div[2]/button"},

        ]
        self.create_gif_process(path_list,"add_furniture")

    def test_update_furniture(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[1]/a"},
            {"path":".//div[1]/div/div[3]/div/div/div[2]/div[1]/div/ul/li/div/div[1]/div/div[3]/div/button[1]"},
            {"path":".//div[3]/div[2]/ul/li[1]/a"},
            {"path":".//div[1]/div/div[3]/div/div/div[1]/form/div[1]/div[1]/div[1]/div/span/span[1]/span"},
            {"path":".//div[1]/div/div[3]/div/div/div[1]/form/div[1]/div[1]/div[1]/div/span/span[1]/span"},
            {"path":".//*[@id='id_name']", "extra_action": "clearinput"},
            {"path":".//*[@id='id_name']", "extra_action": "setvalue","value":"Generico 2"},
            {"path":".//div[1]/div/div[3]/div/div/div[1]/form/div[1]/div[1]/div[3]/div/div/span/span[1]/span"},
            {"path":".//div[1]/div/div[3]/div/div/div[1]/form/div[1]/div[1]/div[3]/div/div/span/span[1]/span"},
            {"path":".//div[1]/div/div[3]/div/div/div[1]/form/div[1]/div[2]/button"},
        ]
        self.create_gif_process(path_list,"update_furniture")
    def test_move_furniture(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[1]/a"},
            {"path":".//div[1]/div/div[3]/div/div/div[2]/div[1]/div/ul/li/div/div[1]/div/div[3]/div/button[1]"},
            {"path":".//div[3]/div[2]/ul/li[1]/a"},
            {"path":".//div[1]/div/div[3]/div/div/div[1]/form/div[1]/div[1]/div[1]/div/span/span[1]/span"},
            {"path": ".//span/span/span[2]/ul/li[3]"},
            {"path":".//*[@id='id_name']", "extra_action": "clearinput"},
            {"path":".//*[@id='id_name']", "extra_action": "setvalue","value":"Generico 2"},
            {"path":".//div[1]/div/div[3]/div/div/div[1]/form/div[1]/div[2]/button"},
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[1]/div/ul/li[2]/div/div[1]/div/div[3]/div/button[1]"},

        ]
        self.create_gif_process(path_list,"move_furniture")

    def test_delete_furniture(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
                {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[1]/a"},
                {"path":".//div[1]/div/div[3]/div/div/div[2]/div[1]/div/ul/li/div/div[1]/div/div[3]/div/button[1]"},
                {"path":".//div[3]/div[2]/ul/li[1]/a"},
                {"path":".//div[1]/div/div[3]/div/div/div[1]/form/div[1]/div[3]/a"},
                {"path":".//div[1]/div/div[3]/div/div/form/input[2]"},
                ]
        self.create_gif_process(path_list,"delete_furniture")

    def test_add_furniture_type(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
                {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[1]/a"},
                {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[1]/div/ul/li/div/div[1]/div/div[3]/div/button[1]"},
                {"path": ".//div[3]/div[2]/ul/li[1]/a"},
                {"path":".//*[@id='add_type_id']"},
                {"path":".//*[@id='id_description']","extra_action":"clearinput"},
                {"path":".//*[@id='id_description']","extra_action":"setvalue", "value": "Recolector"},
                {"path":".//div[3]/div/div/div[3]/button[2]"},
                ]
        self.create_gif_process(path_list,"add_furniture_type")
