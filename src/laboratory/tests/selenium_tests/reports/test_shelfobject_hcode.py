from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse
from organilab_test.tests.base import OptimizedSeleniumBase, modifies_db


class ShelfObjectHcodeSeleniumBase(OptimizedSeleniumBase):
    fixtures = ["selenium/base_selenium.json", "selenium/laboratory_delta.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )
        self.selenium.set_window_size(1920, 1080)

    def navigate_to_hcode_view(self):
        url = self.live_server_url + str(
            reverse(
                "laboratory:shelf_object_hcode",
                kwargs={"org_pk": 1, "lab_pk": 1},
            )
        )
        self.selenium.get(url)
        self.wait_for_page_ready()


@tag("selenium")
class ShelfObjectHcodeSeleniumTest(ShelfObjectHcodeSeleniumBase):

    @modifies_db
    def test_update_process_condition(self):
        """Test updating the process condition of a flammable reactive.

        Flow: Navigate to 'Update process condition of reagents' ->
        Wait for DataTable to load -> Click edit button on first row ->
        Select a process condition in the modal -> Submit form.

        GIF: docs/source/_static/gif/update_process_condition.gif
        """
        self.navigate_to_hcode_view()
        path_list = [
            {
                "path": "//*[@id='tableshelfobject']//tbody/tr[1]",
                "extra_action": "script",
                "value": (
                    "var t=$('#tableshelfobject').DataTable();"
                    "var d=t.row(0).data();"
                    "if(d){ocrud.update(d);}"
                ),
                "sleep": 3,
            },
            {
                "path": "//*[@id='update_obj_form']//div/div/span/span/span",
                "sleep": 1,
            },
            {
                "path": "/html/body/span/span/span[2]/ul/li[2]",
            },
            {
                "path": "//*[@id='update_obj_modal']//button[contains(@class, 'formadd')]",
            },
        ]
        self.create_gif_process(path_list, "update_process_condition")
