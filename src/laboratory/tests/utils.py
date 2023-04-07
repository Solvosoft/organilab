from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils.timezone import now
from djgentelella.models import ChunkedUpload
from django.test import TestCase
from django.test import Client

from auth_and_perms.models import Rol
from laboratory.models import OrganizationStructure, Laboratory
import base64

from laboratory.tests.file_b64 import FILE_B64


def get_file_bytes():
    return base64.b64decode(FILE_B64)


class BaseSetUpTest(TestCase):

    def setUp(self):
        fbytes = get_file_bytes()
        self.chfile = ChunkedUpload.objects.create(
            file=ContentFile(fbytes, name="A file"),
            filename="tests.pdf",
            offset=len(fbytes),
            completed_on=now(),
            user=User.objects.first()
        )


class BaseLaboratorySetUpTest(BaseSetUpTest):
    fixtures = ["laboratory_data.json"]

    def setUp(self):
        super().setUp()

        self.user = get_user_model().objects.filter(username="admin").first()
        self.org = OrganizationStructure.objects.first()
        self.lab = Laboratory.objects.first()
        self.labroom = self.lab.rooms.first()
        self.client.force_login(self.user)

class BaseLaboratoryTasksSetUpTest(BaseSetUpTest):
    fixtures = ["laboratory_tasks_data.json"]

    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.filter(username="admin").first()
        self.org = OrganizationStructure.objects.first()
        self.lab = Laboratory.objects.first()
        self.labroom = self.lab.rooms.first()
        self.client.force_login(self.user)


class BaseOrganizatonManageSetUpTest(BaseSetUpTest):
    fixtures = ["organization_manage_data.json"]

    def setUp(self):
        super().setUp()

        #ORG
        self.org1 = OrganizationStructure.objects.filter(name="Organization 1").first()
        self.org2 = OrganizationStructure.objects.filter(name="Organization 2").first()
        self.org3 = OrganizationStructure.objects.filter(name="Organization 3").first()

        #USER
        self.user1_org1 = get_user_model().objects.filter(username="user1org1").first()
        self.user2_org2 = get_user_model().objects.filter(username="user2org2").first()
        self.user3_org1 = get_user_model().objects.filter(username="user3org1").first()
        self.user4_org2 = get_user_model().objects.filter(username="user4org2").first()

        #PROFILE
        self.profile1_org1 = self.user1_org1.profile
        self.profile2_org2 = self.user2_org2.profile
        self.profile3_org1 = self.user3_org1.profile
        self.profile4_org2 = self.user4_org2.profile

        #ORGS BY USER
        self.user1_org1_list = OrganizationStructure.os_manager.filter_organization_by_user(self.user1_org1).distinct()
        self.user2_org2_list = OrganizationStructure.os_manager.filter_organization_by_user(self.user2_org2).distinct()
        self.user3_org1_list = OrganizationStructure.os_manager.filter_organization_by_user(self.user3_org1).distinct()
        self.user4_org2_list = OrganizationStructure.os_manager.filter_organization_by_user(self.user4_org2).distinct()

        #LABS
        self.lab1_org1 = Laboratory.objects.get(name="Lab 1")
        self.lab2_org2 = Laboratory.objects.get(name="Lab 2")
        self.lab3_org1 = Laboratory.objects.get(name="Lab 3")
        self.lab4_org2 = Laboratory.objects.get(name="Lab 4")

        #INITIAL DATA
        self.role_manage_lab = Rol.objects.get(name="Gestión Laboratorio")
        self.lab_contenttype = ContentType.objects.filter(app_label='laboratory', model='laboratory').first()
        self.org_contenttype = ContentType.objects.filter(app_label='laboratory', model='organizationstructure').first()

class BaseSetUpAjaxRequest(BaseOrganizatonManageSetUpTest):
    def setUp(self):
        super().setUp()

        #CLIENT - LOGIN
        self.client1_org1 = Client()
        self.client2_org2 = Client()
        self.client1_org1.force_login(self.user1_org1)
        self.client2_org2.force_login(self.user2_org2)


class BaseSetUpDjangoRequest(BaseOrganizatonManageSetUpTest):
    fixtures = ["organization_manage_data.json"]

    def setUp(self):
        super().setUp()

        self.org = self.org3