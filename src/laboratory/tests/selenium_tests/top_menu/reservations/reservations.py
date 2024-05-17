from organilab_test.tests.base import SeleniumBase
from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse


@tag('selenium')
class TopMenuSeleniumTest(SeleniumBase):
    fixtures = ["selenium/top_menu.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(user=self.user, driver=self.selenium,
                         base_url=self.live_server_url)
        self.selenium.get(url=self.live_server_url + str(
            reverse('laboratory:labindex', kwargs={"org_pk": 1, "lab_pk": 1})))

        self.path_base = [
            {"path": "//*[@id='reservation_list_id']"}
        ]

    def test_view_reserved_products_lab_index(self):
        path_list = self.path_base + [
            {"path": "//*[@id='table_id_wrapper']", "scroll": "window.scrollTo(0, 50)"}
        ]
        self.create_gif_process(path_list, "reserved_products_lab_index")


    def test_reserve_selected_reserved_products_lab_index(self):
        path_list = self.path_base + [
            {"path": "//*[@id='management_buttons']/input[2]",
             "scroll": "window.scrollTo(0, 50)"}
        ]
        self.create_gif_process(path_list, "reserve_selected_reserved_products_lab_index")

    def test_cancel_selected_reserved_products_lab_index(self):
        path_list = self.path_base + [
            {"path": "//*[@id='management_buttons']/input", "scroll": "window.scrollTo(0, 50)"},
            {"path": "//*[@id='delete_all_obj_reservation_modal']/div/div/div[3]/button[2]"}
        ]
        self.create_gif_process(path_list, "cancel_selected_reserved_products_lab_index")

    def test_delete_reserved_products_lab_index(self):
        path_list = self.path_base + [
            {"path": "//*[@id='table_id']/tbody/tr/td[6]/button", "scroll": "window.scrollTo(0, 50)"},
            {"path": "//*[@id='delete_selected_obj_reservation_modal']/div/div/div[3]/button[2]"}
        ]
        self.create_gif_process(path_list, "delete_reserved_products_lab_index")

