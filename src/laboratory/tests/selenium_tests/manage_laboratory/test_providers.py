from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse

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

    def navigate_to_provider_list(self):
        """Navigate directly to the provider list page."""
        url = self.live_server_url + str(
            reverse("laboratory:provider_view", kwargs={"org_pk": 1, "lab_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def test_view_providers(self):
        """Test viewing the providers list page.

        Flow: Navigate to provider list -> View DataTable with providers.

        GIF: docs/source/_static/gif/view_providers.gif
        """
        self.navigate_to_provider_list()
        path_list = [
            {
                "path": "//h1",
                "screenshot_name": "view_provider",
            },
        ]
        self.create_gif_process(path_list, "view_providers")

    def test_add_provider(self):
        """Test adding a new provider via the create modal.

        Flow: Navigate to provider list -> Click create button ->
        Fill form (name, phone, email, legal identity) -> Save.

        GIF: docs/source/_static/gif/add_provider.gif
        """
        self.navigate_to_provider_list()
        path_list = [
            {
                "path": "//*[@id='table_wrapper']//button[contains(@class, 'btn-outline-success')]",
                "sleep": 1,
            },
            {
                "path": "//input[@id='id_create-name']",
                "extra_action": "clearinput",
                "sleep": 1,
            },
            {
                "path": "//input[@id='id_create-name']",
                "extra_action": "setvalue",
                "value": "Fanal",
            },
            {
                "path": "//input[@id='id_create-phone_number']",
                "extra_action": "clearinput",
            },
            {
                "path": "//input[@id='id_create-phone_number']",
                "extra_action": "setvalue",
                "value": "(506)2234-0000",
            },
            {
                "path": "//input[@id='id_create-email']",
                "extra_action": "clearinput",
            },
            {
                "path": "//input[@id='id_create-email']",
                "extra_action": "setvalue",
                "value": "kcb",
            },
            {
                "path": "//input[@id='id_create-email']",
                "extra_action": "move_cursor_end",
                "reduce_length": 3,
            },
            {
                "path": "//input[@id='id_create-email']",
                "extra_action": "setvalue",
                "value": "@gmail.com",
            },
            {
                "path": "//input[@id='id_create-legal_identity']",
                "extra_action": "clearinput",
            },
            {
                "path": "//input[@id='id_create-legal_identity']",
                "extra_action": "setvalue",
                "value": "123456879",
            },
            {
                "path": "//*[@id='create_obj_modal']//button[contains(@class, 'btn-primary')]",
            },
        ]
        self.create_gif_process(path_list, "add_provider")

    def test_update_provider(self):
        """Test updating an existing provider via the update modal.

        Flow: Navigate to provider list -> Click edit icon on first
        row -> Update phone number and legal identity -> Save.

        GIF: docs/source/_static/gif/update_provider.gif
        """
        self.navigate_to_provider_list()
        path_list = [
            {
                "path": "//*[@id='table']//tbody/tr[1]//i[contains(@class, 'fa-edit')]",
                "sleep": 1,
            },
            {
                "path": "//input[@id='id_update-phone_number']",
                "extra_action": "clearinput",
                "sleep": 1,
            },
            {
                "path": "//input[@id='id_update-phone_number']",
                "extra_action": "setvalue",
                "value": "(506)2234-0000",
            },
            {
                "path": "//input[@id='id_update-legal_identity']",
                "extra_action": "clearinput",
            },
            {
                "path": "//input[@id='id_update-legal_identity']",
                "extra_action": "setvalue",
                "value": "123456879",
            },
            {
                "path": "//*[@id='update_obj_modal']//button[contains(@class, 'btn-primary')]",
            },
        ]
        self.create_gif_process(path_list, "update_provider")
