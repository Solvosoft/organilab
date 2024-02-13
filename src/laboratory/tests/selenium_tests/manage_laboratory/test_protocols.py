from django.core.files.base import ContentFile
from django.utils.timezone import now
from djgentelella.models import ChunkedUpload
from laboratory.tests.utils import get_file_bytes
from organilab_test.tests.base import SeleniumBase
from django.test import tag
from django.contrib.auth.models import User
import json


@tag('selenium')
class ProtocolsSeleniumTest(SeleniumBase):
    fixtures = ["selenium/laboratory_selenium.json"]
    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(user=self.user, driver=self.selenium, base_url=self.live_server_url)
        self.path_base = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[1]/div/div/span/span[1]/span"},
            {"path": "/html/body/span/span/span/ul/li[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div/div/div/a[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div/div/div[1]/a"},
        ]

    def add_chunked(self):
        fbytes = get_file_bytes()
        self.chfile = ChunkedUpload.objects.create(
            file=ContentFile(fbytes, name="A file"), filename="tests.pdf",
            offset=len(fbytes), completed_on=now(), user=self.user)
    def test_view_protocols(self):

        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[2]/ul/li[3]/a"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/h4", "screenshot_name": "protocols_index"},
        ]
        self.create_gif_process(path_list, "view_protocols")

    def test_create_protocol(self):
        self.add_chunked()
        script = "const e = document.querySelector('.chunkedvalue');e.value='%s'" % json.dumps({'token': self.chfile.upload_id, 'name': 'protocol.pdf','display_text': 'protocol_test.pdf'})
        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[2]/ul/li[3]/a"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/a"},
            {"path": "//*[@id='id_name']", "extra_action":"clearInput"},
            {"path": "//*[@id='id_name']", "extra_action":"setvalue","value":"Radiación"},
            {"path": "//*[@id='id_short_description']", "extra_action":"clearInput"},
            {"path": "//*[@id='id_short_description']", "extra_action":"setvalue","value":"Evitar tocar envases"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div/form/div[3]/div/div/div[1]/div[4]", "extra_action":"script",
             "value":script},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div/form/div[4]/button"},
        ]
        self.create_gif_process(path_list, "add_protocol")

    def test_update_protocol(self):
        self.add_chunked()
        script = "const e = document.querySelector('.chunkedvalue');e.value='%s'" % json.dumps({'token': self.chfile.upload_id, 'name': 'protocol.pdf','display_text': 'protocol_test.pdf'})
        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[2]/ul/li[3]/a"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div[2]/div/table/tbody/tr/td[4]/a[1]"},
            {"path": "//*[@id='id_name']", "extra_action":"clearInput"},
            {"path": "//*[@id='id_name']", "extra_action":"setvalue","value":"Radiación"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div/form/div[3]/div/div/div[1]/div[4]", "extra_action":"script",
             "value":script},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div/form/div[4]/button"},
        ]
        self.create_gif_process(path_list, "update_protocol")

    def test_delete_protocol(self):
        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[2]/ul/li[3]/a"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div[2]/div/table/tbody/tr/td[4]/a[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/form/input[2]"},
        ]
        self.create_gif_process(path_list, "delete_protocol")

    def test_download_protocol(self):
        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[2]/ul/li[3]/a"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div[2]/div/table/tbody/tr/td[3]/a"},
        ]
        self.create_gif_process(path_list, "download_protocol")
