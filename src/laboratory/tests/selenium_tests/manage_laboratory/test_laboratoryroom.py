from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse

from laboratory.models import OrganizationStructure
from organilab_test.tests.base import SeleniumBase


@tag('selenium')
class LabRoomSeleniumTest(SeleniumBase):
    fixtures = ["selenium/laboratory_selenium.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.org = OrganizationStructure.objects.get(pk=1)
        self.select_org_url = self.live_server_url + str(reverse('auth_and_perms:select_organization_by_user'))
        self.force_login(user=self.user, driver=self.selenium, base_url=self.live_server_url)

    def view_laboratory_rooms(self):
        path_list = [
            {"path": ".//div[1]/div/div[3]/div/div/div/div[1]/div/div/span"},
            {"path": ".//span/span/span[2]/ul/li[1]"},
            {"path": ".//div[1]/div/div[3]/div/div/div/div[2]/div/div/div/a[1]"},
            {"path": ".//div[1]/div/div[3]/div/div/div/div[1]/div[1]/div/div/div[1]/a"},
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[1]/a"},
        ]
        self.create_gif_process(path_list, "view_room")

    def view_laboratory_rooms_navbar(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": ".//div[1]/div/div[2]/nav/div[1]/ul[2]/li[6]"},
            {"path":".//div[1]/div/div[2]/nav/div[1]/ul[2]/li[6]/ul/li[5]/a"}
        ]
        self.create_gif_process(path_list, "view_room_navbar")


    def add_laboratory_rooms(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        self.path_base = [
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[1]/a"},
            {"path": ".//*[@id='id_name']", "extra_action":"clearinput"},
            {"path": ".//*[@id='id_name']", "extra_action":"setvalue", "value":"Nuevo Cuarto"},
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[1]/form/div[2]/div/button"},
        ]
        self.create_gif_process(self.path_base, "add_room")
    def update_laboratory_rooms(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        self.path_base = [
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[1]/a"},
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[1]/div/ul/li[3]/div/div[2]/div/a[1]"},
            {"path": ".//*[@id='id_name']", "extra_action":"clearinput"},
            {"path": ".//*[@id='id_name']", "extra_action":"setvalue", "value":"Cuarto Actualizado"},
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[1]/form/div[2]/div/button"},
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[1]/form/div[2]/div/button"},
        ]
        self.create_gif_process(self.path_base, "update_room")

    def delete_laboratory_rooms(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        self.path_base = [
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[1]/a"},
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[1]/div/ul/li[3]/div/div[2]/div/a[2]"},
            {"path": ".//div[1]/div/div[3]/div/div/form/input[2]"},
            {"path": ".//*[@id='id_name']", "extra_action": "clearinput"},
        ]
        self.create_gif_process(self.path_base, "delete_room")

    def test_laboratory_room_crud(self):
        self.view_laboratory_rooms()
        self.add_laboratory_rooms()
        self.update_laboratory_rooms()
        self.delete_laboratory_rooms()
        self.view_laboratory_rooms_navbar()

    def test_update_qr(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        self.path_base = [
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[1]/a"},
            {"path": "./html/body/div[1]/div/div[3]/div/div/div[2]/a", "screenshot_name":"update_qr"},
        ]
        self.create_gif_process(self.path_base, "update_qr")
