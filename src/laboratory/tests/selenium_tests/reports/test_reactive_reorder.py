from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse
from organilab_test.tests.base import OptimizedSeleniumBase, modifies_db


class ReactiveReorderSeleniumBase(OptimizedSeleniumBase):
    fixtures = ["selenium/base_selenium.json", "selenium/laboratory_delta.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )
        self.selenium.set_window_size(1920, 1080)

    def navigate_to_lab_index(self):
        url = self.live_server_url + str(
            reverse("laboratory:labindex", kwargs={"org_pk": 1, "lab_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_reactive_reorder(self):
        url = self.live_server_url + str(
            reverse("laboratory:shel_objects_reactives", kwargs={"org_pk": 1, "lab_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()


@tag("selenium")
class ReactiveReorderSeleniumTest(ReactiveReorderSeleniumBase):

    @modifies_db
    def test_increase_reactive(self):
        """Test increasing the quantity of a reactive from the lab index menu.

        Flow: Navigate to lab index -> Click 'Consumption reorder' link ->
        Wait for DataTable to load -> Click increase button (fa-plus) on first
        row -> Fill amount and description in modal -> Select measurement unit
        -> Submit form.

        GIF: docs/source/_static/gif/increase_reactive.gif
        """
        self.navigate_to_lab_index()
        self.navigate_to_reactive_reorder()
        path_list = [
            {
                "path": "//*[@id='table']//tbody/tr[1]",
                "extra_action": "script",
                "value": "$('#table tbody tr:first').find('.fa-plus').closest('a, button').trigger('click');",
                "wait_ready": True,
                "sleep": 3,
            },
            {
                "path": "//*[@id='table']//tbody/tr[1]",
                "extra_action": "script",
                "value": "$('#table tbody tr:first').find('.fa-plus').trigger('click');",
                "wait_ready": True,
                "sleep": 3,
            },
            {
                "path": "//*[@id='increasesomodal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": (
                    "var opt=new Option('Mililitros',63,true,true);"
                    "$('#id_increase-measurement_unit').append(opt).trigger('change');"
                ),
                "sleep": 1,
            },
            {
                "path": "//*[@id='id_increase-amount']",
                "extra_action": "clearinput",
            },
            {
                "path": "//*[@id='id_increase-amount']",
                "extra_action": "setvalue",
                "value": "5",
            },
            {
                "path": "//*[@id='id_increase-description']",
                "extra_action": "clearinput",
            },
            {
                "path": "//*[@id='id_increase-description']",
                "extra_action": "setvalue",
                "value": "Reposicion de reactivo para experimentos.",
            },
            {
                "path": "//*[@id='increasesomodal']//button[contains(@class, 'formadd')]",
            },
        ]
        self.create_gif_process(path_list, "increase_reactive")

    @modifies_db
    def test_decrease_reactive(self):
        """Test decreasing the quantity of a reactive from the lab index menu.

        Flow: Navigate to lab index -> Click 'Consumption reorder' link ->
        Wait for DataTable to load -> Click decrease button (fa-minus) on first
        row -> Fill amount and description in modal -> Select measurement unit
        -> Submit form.

        GIF: docs/source/_static/gif/decrease_reactive.gif
        """
        self.navigate_to_lab_index()
        self.navigate_to_reactive_reorder()
        path_list = [
            {
                "path": "//*[@id='table']//tbody/tr[1]",
                "extra_action": "script",
                "value": "$('#table tbody tr:first').find('.fa-minus').closest('a, button').trigger('click');",
                "wait_ready": True,
                "sleep": 3,
            },
            {
                "path": "//*[@id='table']//tbody/tr[1]",
                "extra_action": "script",
                "value": "$('#table tbody tr:first').find('.fa-minus').trigger('click');",
                "wait_ready": True,
                "sleep": 3,
            },
            {
                "path": "//*[@id='decreasesomodal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": (
                    "var opt=new Option('Mililitros',63,true,true);"
                    "$('#id_decrease-measurement_unit').append(opt).trigger('change');"
                ),
                "sleep": 1,
            },
            {
                "path": "//*[@id='id_decrease-amount']",
                "extra_action": "clearinput",
            },
            {
                "path": "//*[@id='id_decrease-amount']",
                "extra_action": "setvalue",
                "value": "2",
            },
            {
                "path": "//*[@id='id_decrease-description']",
                "extra_action": "clearinput",
            },
            {
                "path": "//*[@id='id_decrease-description']",
                "extra_action": "setvalue",
                "value": "Consumo de reactivo en practica de laboratorio.",
            },
            {
                "path": "//*[@id='decreasesomodal']//button[contains(@class, 'formadd')]",
            },
        ]
        self.create_gif_process(path_list, "decrease_reactive")
