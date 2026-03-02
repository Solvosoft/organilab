from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse

from laboratory.models import OrganizationStructure
from organilab_test.tests.base import OptimizedSeleniumBase, modifies_db


@tag("selenium")
class LabRoomSeleniumTest(OptimizedSeleniumBase):
    fixtures = ["selenium/base_selenium.json", "selenium/laboratory_delta.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.org = OrganizationStructure.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )

    def navigate_to_rooms_create(self):
        """Navigate directly to the laboratory room create/manage page."""
        url = self.live_server_url + str(
            reverse("laboratory:rooms_create", kwargs={"org_pk": 1, "lab_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_rooms_list(self):
        """Navigate directly to the laboratory room tree view."""
        url = self.live_server_url + str(
            reverse("laboratory:rooms_list", kwargs={"org_pk": 1, "lab_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_lab_index(self):
        """Navigate directly to the laboratory index page."""
        url = self.live_server_url + str(
            reverse("laboratory:labindex", kwargs={"org_pk": 1, "lab_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def view_laboratory_rooms(self):
        """View the laboratory rooms tree page.

        Flow: Navigate to rooms list -> View room tree.

        GIF: docs/source/_static/gif/view_room.gif
        """
        self.navigate_to_rooms_list()
        path_list = [
            {
                "path": "//h1",
            },
        ]
        self.create_gif_process(path_list, "view_room")

    def view_laboratory_rooms_navbar(self):
        """View laboratory rooms from the navbar dropdown.

        Flow: Navigate to lab index -> Click rooms link in view
        section.

        GIF: docs/source/_static/gif/view_room_navbar.gif
        """
        self.navigate_to_lab_index()
        path_list = [
            {
                "path": "//a[contains(@href, 'rooms') and .//strong]",
                "sleep": 1,
            },
        ]
        self.create_gif_process(path_list, "view_room_navbar")

    def add_laboratory_rooms(self):
        """Add a new laboratory room.

        Flow: Navigate to room management -> Fill room name ->
        Submit create form.

        GIF: docs/source/_static/gif/add_room.gif
        """
        self.navigate_to_rooms_create()
        path_list = [
            {
                "path": "//*[@id='id_name']",
                "extra_action": "clearinput",
            },
            {
                "path": "//*[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Nuevo Cuarto",
            },
            {
                "path": "//form//button[contains(@class, 'btn-outline-success')]",
            },
        ]
        self.create_gif_process(path_list, "add_room")

    def update_laboratory_rooms(self):
        """Update an existing laboratory room.

        Flow: Navigate to room management -> Click edit button
        on a room -> Clear and enter new name -> Submit.

        GIF: docs/source/_static/gif/update_room.gif
        """
        self.navigate_to_rooms_create()
        path_list = [
            {
                "path": "//ul[contains(@class, 'list-group')]//a[contains(@class, 'btn-outline-warning')]",
            },
            {
                "path": "//*[@id='id_name']",
                "extra_action": "clearinput",
                "wait_ready": True,
            },
            {
                "path": "//*[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Cuarto Actualizado",
            },
            {
                "path": "//form//button[contains(@class, 'btn-outline-warning')]",
            },
        ]
        self.create_gif_process(path_list, "update_room")

    def delete_laboratory_rooms(self):
        """Delete a laboratory room.

        Flow: Navigate to room management -> Click delete button
        on a room -> Confirm deletion.

        GIF: docs/source/_static/gif/delete_room.gif
        """
        self.navigate_to_rooms_create()
        path_list = [
            {
                "path": "//ul[contains(@class, 'list-group')]//a[contains(@class, 'btn-outline-danger')]",
            },
            {
                "path": "//input[@type='submit' and contains(@class, 'btn-danger')]",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "delete_room")

    @modifies_db
    def test_laboratory_room_crud(self):
        """Test full CRUD cycle for laboratory rooms.

        Chains: view rooms -> add room -> update room -> delete room
        -> view rooms from navbar.
        """
        self.view_laboratory_rooms()
        self.add_laboratory_rooms()
        self.update_laboratory_rooms()
        self.delete_laboratory_rooms()
        self.view_laboratory_rooms_navbar()

    def test_update_qr(self):
        """Test viewing the QR code rebuild page.

        Flow: Navigate to room management -> Click rebuild QR link.

        GIF: docs/source/_static/gif/update_qr.gif
        """
        self.navigate_to_rooms_create()
        path_list = [
            {
                "path": "//a[contains(@href, 'rebuild_laboratory_qr')]",
                "screenshot_name": "update_qr",
            },
        ]
        self.create_gif_process(path_list, "update_qr")
