from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse
from laboratory.models import OrganizationStructure
from organilab_test.tests.base import SeleniumBase


@tag('selenium')
class ShelvesSeleniumTest(SeleniumBase):
    fixtures = ["selenium/laboratory_selenium.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.org = OrganizationStructure.objects.get(pk=1)
        self.select_org_url = self.live_server_url + str(reverse('auth_and_perms:select_organization_by_user'))
        self.force_login(user=self.user, driver=self.selenium, base_url=self.live_server_url)

    def test_create_shelf(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[1]/a"},
            {"path":".//div[1]/div/div[3]/div/div/div[2]/div[1]/div/ul/li/div/div[1]/div/div[3]/div/button[1]"},
            {"path":".//div[3]/div[2]/ul/li[1]/a"},
            {"path":".//div[1]/div/div[3]/div/div/div[1]/form/div[2]/div/div[1]/button[1]/span", "screenshot_name":"view_shelves"},
            {"path":"/html/body/div[1]/div/div[3]/div/div/div[1]/form/div[2]/table/tr/td/a"},
            {"path":".//*[@id='id_shelf--name']", "extra_action": "clearinput"},
            {"path":".//*[@id='id_shelf--name']",  "extra_action": "setvalue","value":"Primer Estante"},
            {"path":".//div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/form/div[1]/div[2]/div/div/span/span[1]/span"},
            {"path": ".//span/span/span[2]/ul/li[2]"},
            {"path": ".//div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/form/div[1]/div[7]/div/span/span[1]/span"},
            {"path": ".//span/span/span[2]/ul/li[2]"},
            {"path": ".//div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/form/div[2]/button[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/form/div[1]/div[2]/button"},

        ]
        self.create_gif_process(path_list,"add_shelf")

    def test_add_cols_rows(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[1]/a"},
            {"path":".//div[1]/div/div[3]/div/div/div[2]/div[1]/div/ul/li/div/div[1]/div/div[3]/div/button[1]"},
            {"path":".//div[3]/div[2]/ul/li[2]/a"},
            {"path":".//div[1]/div/div[3]/div/div/div[1]/form/div[2]/div/div[1]/button[1]/span", "scroll":"window.scrollTo(0, 100)"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/form/div[2]/div/div[1]/button[2]/span"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/form/div[2]/div/div[2]/button[2]/span"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/form/div[2]/div/div[2]/button[1]/span"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/form/div[2]/div/div[2]/button[1]/span","screenshot_name":"remove_shelf_row"},
        ]
        self.create_gif_process(path_list,"manage_rows_cols")

    def test_remove_row_with_shelf(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[1]/a"},
            {"path":".//div[1]/div/div[3]/div/div/div[2]/div[1]/div/ul/li/div/div[1]/div/div[3]/div/button[1]"},
            {"path":".//div[3]/div[2]/ul/li[2]/a"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/form/div[2]/div/div[2]/button[1]/span"},
            {"path": "//*[@id='remove_shelf']","screenshot_name":"remove_shelf_row"},

        ]
        self.create_gif_process(path_list,"manage_rows_cols_shelf")


    def test_update_shelf(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[1]/a"},
            {"path":".//div[1]/div/div[3]/div/div/div[2]/div[1]/div/ul/li/div/div[1]/div/div[3]/div/button[1]"},
            {"path":".//div[3]/div[2]/ul/li[2]/a"},
            {"path":"/html/body/div[1]/div/div[3]/div/div/div[1]/form/div[2]/table/tbody/tr/td/div/ul/li/div/ul/li[1]/a"},
            {"path":".//*[@id='id_shelf--name']", "extra_action": "clearinput"},
            {"path":".//*[@id='id_shelf--name']",  "extra_action": "setvalue","value":"Estante Actualizado"},
            {"path": ".//div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/form/div[1]/div[2]/div/div/span/span[1]/span"},
            {"path": ".//span/span/span[2]/ul/li[3]"},
            {"path": ".//div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/form/div[2]/button[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/form/div[1]/div[2]/button"},

        ]
        self.create_gif_process(path_list,"update_shelf")

    def test_delete_shelf(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[1]/a"},
            {"path":".//div[1]/div/div[3]/div/div/div[2]/div[1]/div/ul/li/div/div[1]/div/div[3]/div/button[1]"},
            {"path":".//div[3]/div[2]/ul/li[2]/a"},
            {"path":"/html/body/div[1]/div/div[3]/div/div/div[1]/form/div[2]/table/tbody/tr/td[1]/div/ul/li/div/ul/li[2]/a"},
            {"path":"/html/body/div[4]/div/div[3]/button[1]"},
        ]
        self.create_gif_process(path_list,"delete_shelf")

    def test_view_shelf(self):
        self.selenium.get(url= self.live_server_url + str(reverse('auth_and_perms:select_organization_by_user')))
        path_list = [
            {"path": ".//div[1]/div/div[3]/div/div/div/div[1]/div/div/span"},
            {"path": ".//span/span/span[2]/ul/li[1]"},
            {"path": ".//div[1]/div/div[3]/div/div/div/div[2]/div/div/div/a[1]"},
            {"path": ".//div[1]/div/div[3]/div/div/div/div[1]/div[1]/div/div/div[1]/a"},
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[1]/a"},
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[1]/div/ul/li/div/div[1]/div/div[3]/div/button[1]"},
            {"path": ".//div[3]/div[2]/ul/li[2]/a"},
        ]
        self.create_gif_process(path_list,"view_shelves")
