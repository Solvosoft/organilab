import json

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import tag
from django.urls import reverse
from django.utils.timezone import now
from djgentelella.models import ChunkedUpload

from laboratory.tests.utils import get_file_bytes
from organilab_test.tests.base import SeleniumBase


@tag("selenium")
class ProtocolsSeleniumTest(SeleniumBase):
    fixtures = ["selenium/laboratory_selenium.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )

    def navigate_to_protocol_list(self):
        """Navigate directly to the protocol list page."""
        url = self.live_server_url + str(
            reverse("laboratory:protocol_list", kwargs={"org_pk": 1, "lab_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def add_chunked(self):
        """Create a ChunkedUpload object for file upload tests."""
        fbytes = get_file_bytes()
        self.chfile = ChunkedUpload.objects.create(
            file=ContentFile(fbytes, name="A file"),
            filename="tests.pdf",
            offset=len(fbytes),
            completed_on=now(),
            user=self.user,
        )

    def test_view_protocols(self):
        """Test viewing the protocols list page.

        Flow: Navigate to protocol list -> View DataTable with protocols.

        GIF: docs/source/_static/gif/view_protocols.gif
        """
        self.navigate_to_protocol_list()
        path_list = [
            {
                "path": "//h4",
                "screenshot_name": "protocols_index",
            },
        ]
        self.create_gif_process(path_list, "view_protocols")

    def test_create_protocol(self):
        """Test creating a new protocol with file upload.

        Flow: Navigate to protocol list -> Click 'Upload' button ->
        Fill form (name, short description, file via chunked upload)
        -> Submit.

        GIF: docs/source/_static/gif/add_protocol.gif
        """
        self.add_chunked()
        script = (
            "const e = document.querySelector('.chunkedvalue');e.value='%s'"
            % json.dumps(
                {
                    "token": self.chfile.upload_id,
                    "name": "protocol.pdf",
                    "display_text": "protocol_test.pdf",
                }
            )
        )
        self.navigate_to_protocol_list()
        path_list = [
            {
                "path": "//a[contains(@class, 'btn-outline-success') and contains(@href, '/protocols/create')]",
                "wait_ready": True,
                "sleep": 1,
            },
            {
                "path": "//*[@id='id_name']",
                "extra_action": "clearinput",
                "wait_ready": True,
            },
            {
                "path": "//*[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Radiación",
            },
            {
                "path": "//*[@id='id_short_description']",
                "extra_action": "clearinput",
            },
            {
                "path": "//*[@id='id_short_description']",
                "extra_action": "setvalue",
                "value": "Evitar tocar envases",
            },
            {
                "path": "//form",
                "extra_action": "script",
                "value": script,
            },
            {
                "path": "//button[@type='submit' and contains(@class, 'btn-primary')]",
            },
        ]
        self.create_gif_process(path_list, "add_protocol")

    def test_update_protocol(self):
        """Test updating an existing protocol.

        Flow: Navigate to protocol list -> Click edit button on first
        row -> Update name and file -> Submit.

        GIF: docs/source/_static/gif/update_protocol.gif
        """
        self.add_chunked()
        script = (
            "const e = document.querySelector('.chunkedvalue');e.value='%s'"
            % json.dumps(
                {
                    "token": self.chfile.upload_id,
                    "name": "protocol.pdf",
                    "display_text": "protocol_test.pdf",
                }
            )
        )
        self.navigate_to_protocol_list()
        path_list = [
            {
                "path": "//table[@id='protocolTable']//tbody/tr[1]//a[contains(@class, 'btn-outline-warning')]",
                "wait_ready": True,
                "sleep": 3,
            },
            {
                "path": "//*[@id='id_name']",
                "extra_action": "clearinput",
                "wait_ready": True,
            },
            {
                "path": "//*[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Radiación",
            },
            {
                "path": "//form",
                "extra_action": "script",
                "value": script,
            },
            {
                "path": "//button[@type='submit' and contains(@class, 'btn-primary')]",
            },
        ]
        self.create_gif_process(path_list, "update_protocol")

    def test_delete_protocol(self):
        """Test deleting a protocol.

        Flow: Navigate to protocol list -> Click delete button on
        first row -> Confirm deletion.

        GIF: docs/source/_static/gif/delete_protocol.gif
        """
        self.navigate_to_protocol_list()
        path_list = [
            {
                "path": "//table[@id='protocolTable']//tbody/tr[1]//a[contains(@class, 'btn-outline-danger')]",
                "sleep": 2,
            },
            {
                "path": "//input[@type='submit' and contains(@class, 'btn-danger')]",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "delete_protocol")

    def test_download_protocol(self):
        """Test downloading a protocol file.

        Flow: Navigate to protocol list -> Click download link on
        first row.

        GIF: docs/source/_static/gif/download_protocol.gif
        """
        self.navigate_to_protocol_list()
        path_list = [
            {
                "path": "//table[@id='protocolTable']//tbody/tr[1]/td[3]//a",
                "sleep": 2,
            },
        ]
        self.create_gif_process(path_list, "download_protocol")
