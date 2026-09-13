from django.contrib.auth.models import User
from django.test import tag
from organilab_test.tests.selenium_xpaths import select2_result
from django.urls import reverse

from organilab_test.tests.base import OptimizedSeleniumBase, modifies_db


class LaboratorySeleniumBase(OptimizedSeleniumBase):
    fixtures = ["selenium/base_selenium.json", "selenium/laboratory_delta.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )

    def navigate_to_register_user_qr_list(self):
        """Navigate directly to the register user QR list page."""
        url = self.live_server_url + str(
            reverse(
                "laboratory:list_register_user_qr",
                kwargs={"org_pk": 1, "lab_pk": 1},
            )
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_register_user_qr_create(self):
        """Navigate directly to the register user QR create page."""
        url = self.live_server_url + str(
            reverse(
                "laboratory:manage_register_user_qr",
                kwargs={"org_pk": 1, "lab_pk": 1, "pk": 0},
            )
        )
        self.selenium.get(url)
        self.wait_for_page_ready()


@tag("selenium")
class RegisterUserQRSeleniumTest(LaboratorySeleniumBase):

    def test_view_register_user_qr(self):
        """Test viewing the register user QR list page.

        Flow: Navigate to register user QR list -> View table.

        GIF: docs/source/_static/gif/view_register_user_QR.gif
        """
        self.navigate_to_register_user_qr_list()
        path_list = [
            {
                "path": "//h2 | //div[contains(@class, 'card-title')]",
                "screenshot_name": "registter_user_QR",
            },
        ]
        self.create_gif_process(path_list, "view_register_user_QR")

    @modifies_db
    def test_create_register_user_qr(self):
        """Test creating a new register user QR entry.

        Flow: Navigate to register user QR list -> Click create
        button -> Select role -> Select organization -> Fill code
        -> Submit.

        GIF: docs/source/_static/gif/create_register_user_QR.gif
        """
        self.navigate_to_register_user_qr_list()
        path_list = [
            {
                "path": "//a[contains(@class, 'btn-outline-primary') and contains(@href, 'manage')]",
            },
            {
                "path": "//select[@id='id_role']/..//span[contains(@class, 'select2-selection')]",
                "wait_ready": True,
                "sleep": 1,
            },
            {
                "path": select2_result(1),
            },
            {
                "path": "//select[@id='id_organization_register']/..//span[contains(@class, 'select2-selection')]",
                "sleep": 1,
            },
            {
                "path": select2_result(1),
            },
            {
                "path": "//*[@id='id_code']",
                "extra_action": "clearinput",
            },
            {
                "path": "//*[@id='id_code']",
                "extra_action": "setvalue",
                "value": "A456",
            },
            {
                "path": "//input[@type='submit' and contains(@class, 'btn-success')]",
            },
        ]
        self.create_gif_process(path_list, "create_register_user_QR")

    @modifies_db
    def test_update_register_user_qr(self):
        """Test updating an existing register user QR entry.

        Flow: Navigate to register user QR list -> Click edit button
        on first row -> Change role -> Change organization -> Submit.

        GIF: docs/source/_static/gif/update_register_user_QR.gif
        """
        self.navigate_to_register_user_qr_list()
        path_list = [
            {
                "path": "//table[@id='form_table']//tbody/tr[1]//a[contains(@class, 'btn-outline-warning')]",
            },
            {
                "path": "//select[@id='id_role']/..//span[contains(@class, 'select2-selection')]",
                "wait_ready": True,
                "sleep": 1,
            },
            {
                "path": select2_result(2),
            },
            {
                "path": "//select[@id='id_organization_register']/..//span[contains(@class, 'select2-selection')]",
                "sleep": 1,
            },
            {
                "path": select2_result(2),
            },
            {
                "path": "//input[@type='submit' and contains(@class, 'btn-success')]",
            },
        ]
        self.create_gif_process(path_list, "update_register_user_QR")

    @modifies_db
    def test_delete_register_user_qr(self):
        """Test deleting a register user QR entry.

        Flow: Navigate to register user QR list -> Click delete
        button on first row -> Confirm deletion.

        GIF: docs/source/_static/gif/delete_register_user_QR.gif
        """
        self.navigate_to_register_user_qr_list()
        path_list = [
            {
                "path": "//table[@id='form_table']//tbody/tr[1]//a[contains(@class, 'btn-outline-danger')]",
            },
            {
                "path": "//input[@type='submit' and contains(@class, 'btn-danger')]",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "delete_register_user_QR")

    def test_downlooad_register_user_qr(self):
        """Test downloading a register user QR PDF.

        Flow: Navigate to register user QR list -> Click download
        button on first row.

        GIF: docs/source/_static/gif/download_register_user_QR.gif
        """
        self.navigate_to_register_user_qr_list()
        path_list = [
            {
                "path": "//table[@id='form_table']//tbody/tr[1]//a[contains(@class, 'btn-outline-info')]",
            },
        ]
        self.create_gif_process(path_list, "download_register_user_QR")

    def test_logentry_register_user_qr(self):
        """Test viewing log entries for a register user QR.

        Flow: Navigate to register user QR list -> Click history
        button on first row.

        GIF: docs/source/_static/gif/logentry_register_user_QR.gif
        """
        self.navigate_to_register_user_qr_list()
        path_list = [
            {
                "path": "//table[@id='form_table']//tbody/tr[1]//a[contains(@class, 'btn-outline-success')]",
            },
        ]
        self.create_gif_process(path_list, "logentry_register_user_QR")
