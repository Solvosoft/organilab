from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse

from organilab_test.tests.base import SeleniumBase


class InformSeleniumBase(SeleniumBase):
    fixtures = ["selenium/laboratory_selenium.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )

    def navigate_to_inform_list(self):
        """Navigate directly to the inform list page."""
        url = self.live_server_url + str(
            reverse(
                "laboratory:get_informs",
                kwargs={"org_pk": 1, "lab_pk": 1},
            )
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_complete_inform(self, pk=15):
        """Navigate directly to the complete/review inform page."""
        url = self.live_server_url + str(
            reverse(
                "laboratory:complete_inform",
                kwargs={"org_pk": 1, "lab_pk": 1, "pk": pk},
            )
        )
        self.selenium.get(url)
        self.wait_for_page_ready()


@tag("selenium")
class InformSeleniumTest(InformSeleniumBase):

    def test_view_inform(self):
        """Test viewing the inform list page.

        Flow: Navigate to inform list -> View page with DataTable.

        GIF: docs/source/_static/gif/view_inform.gif
        """
        self.navigate_to_inform_list()
        path_list = [
            {
                "path": "//h3//span | //h3",
                "screenshot_name": "view_informs",
            },
        ]
        self.create_gif_process(path_list, "view_inform")

    def test_add_inform(self):
        """Test adding a new inform.

        Flow: Navigate to inform list -> Click add button -> Fill name
        -> Select template via Select2 -> Submit.

        GIF: docs/source/_static/gif/add_inform.gif
        """
        self.navigate_to_inform_list()
        path_list = [
            {
                "path": "//a[contains(@class, 'create_btn') and @data-bs-target='#add_inform']",
                "sleep": 1,
            },
            {
                "path": "//*[@id='add_inform']//input[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Prime Informe",
                "sleep": 1,
            },
            {
                "path": "//*[@id='add_inform']//span[contains(@class, 'select2-selection')]",
                "sleep": 1,
            },
            {
                "path": "//ul[contains(@class, 'select2-results__options')]/li[3]",
            },
            {
                "path": "//*[@id='add_inform']//button[@type='submit' and contains(@class, 'btn-primary')]",
            },
        ]
        self.create_gif_process(path_list, "add_inform")

    def test_review_inform(self):
        """Test reviewing an inform and sending it for review.

        Flow: Navigate to complete inform page -> Fill formio form
        fields -> Click 'Send for review' -> Confirm in SweetAlert
        -> Chain finalize.

        GIF: docs/source/_static/gif/review_inform.gif
        """
        self.navigate_to_complete_inform(pk=15)
        path_list = [
            {
                "path": "//*[@id='formio']//input[1]",
                "extra_action": "clearinput",
                "sleep": 2,
            },
            {
                "path": "//*[@id='formio']//input[1]",
                "extra_action": "setvalue",
                "value": "Primer Laboratorio",
            },
            {
                "path": "//*[@id='formio']//textarea[1]",
                "extra_action": "clearinput",
            },
            {
                "path": "//*[@id='formio']//textarea[1]",
                "extra_action": "setvalue",
                "value": "Caída de estante de reactivos",
            },
            {
                "path": "//button[contains(@onclick, 'saveForm')]",
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 1,
            },
        ]
        self.create_gif_process(path_list, "review_inform")
        self.finalize_inform()

    def test_remove_inform(self):
        """Test removing an inform from the list.

        Flow: Navigate to inform list -> Click delete button on first
        row -> View result.

        GIF: docs/source/_static/gif/remove_inform.gif
        """
        self.navigate_to_inform_list()
        path_list = [
            {
                "path": "//table[@id='inform']//tbody/tr[1]//a[contains(@class, 'btn-outline-danger')]",
            },
            {
                "path": "//h3//span | //h3",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "remove_inform")

    def test_crud_inform_observation(self):
        """Test adding an observation/comment to an inform.

        Flow: Navigate to complete inform page -> Toggle observations
        panel -> Click add comment -> Enter comment text in SweetAlert
        -> Confirm -> View comment.

        GIF: docs/source/_static/gif/add_inform_observation.gif
        """
        self.navigate_to_complete_inform(pk=15)
        path_list = [
            {
                "path": "//*[@id='observation']",
                "sleep": 2,
            },
            {
                "path": "//*[@id='panelobservaciones']//button[contains(@onclick, 'save_comment')]",
                "sleep": 1,
            },
            {
                "path": "//div[contains(@class, 'swal2-popup')]//textarea",
                "extra_action": "setvalue",
                "value": "Primer comentario",
                "sleep": 1,
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 1,
            },
            {
                "path": "//*[@id='listado']//div[contains(@class, 'container')]",
            },
        ]
        self.create_gif_process(path_list, "add_inform_observation")
        self.edit_inform_observation()
        self.remove_inform_observation()

    def edit_inform_observation(self):
        """Edit an existing inform observation.

        Flow: Click edit icon on comment -> Clear and enter new text
        in SweetAlert -> Confirm -> Dismiss success alert.

        GIF: docs/source/_static/gif/edit_inform_observation.gif
        """
        path_list = [
            {
                "path": "//*[@id='listado']//i[contains(@class, 'beditbtn')]",
                "sleep": 1,
            },
            {
                "path": "//div[contains(@class, 'swal2-popup')]//textarea",
                "extra_action": "clearinput",
                "sleep": 1,
            },
            {
                "path": "//div[contains(@class, 'swal2-popup')]//textarea",
                "extra_action": "setvalue",
                "value": "Comentario Actualizado.",
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 1,
            },
            {
                "path": "//*[@id='listado']//div[contains(@class, 'container')]",
            },
        ]
        self.create_gif_process(path_list, "edit_inform_observation")

    def remove_inform_observation(self):
        """Remove an observation from an inform.

        Flow: Click delete icon on comment -> Confirm in SweetAlert
        -> Dismiss success alert.

        GIF: docs/source/_static/gif/remove_inform_observation.gif
        """
        path_list = [
            {
                "path": "//*[@id='listado']//i[contains(@class, 'deletebtn')]",
                "sleep": 1,
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 1,
            },
        ]
        self.create_gif_process(path_list, "remove_inform_observation")

    def finalize_inform(self):
        """Finalize an inform after review.

        Flow: Navigate to inform list -> Click complete button on first
        row -> Click finalize button -> Confirm in SweetAlert.

        GIF: docs/source/_static/gif/finalize_inform.gif
        """
        self.navigate_to_inform_list()
        path_list = [
            {
                "path": "//table[@id='inform']//tbody/tr[1]//a[contains(@class, 'btn-outline-success')]",
                "sleep": 2,
            },
            {
                "path": "//button[contains(@onclick, 'saveForm')]",
                "wait_ready": True,
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 1,
            },
        ]
        self.create_gif_process(path_list, "finalize_inform")
