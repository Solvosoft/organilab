from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils.timezone import now
from djgentelella.models import ChunkedUpload
from django.test import TestCase

from laboratory.models import OrganizationStructure, Laboratory
import base64

from laboratory.tests.file_b64 import FILE_B64


def get_file_bytes():
    return base64.b64decode(FILE_B64)


class BaseSetUpTest(TestCase):
    fixtures = ["../fixtures/initialdata.json", "../fixtures/laboratory_data.json"]

    def setUp(self):
        self.user = get_user_model().objects.filter(username="german").first()
        self.org = OrganizationStructure.objects.first()
        self.lab = Laboratory.objects.first()
        self.client.force_login(self.user)
        fbytes = get_file_bytes()
        self.chfile = ChunkedUpload.objects.create(
            file=ContentFile(fbytes, name="A file"),
            filename="tests.pdf",
            offset=len(fbytes),
            completed_on=now(),
            user=self.user
        )