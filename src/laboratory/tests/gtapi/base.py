from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, Client

from laboratory.models import OrganizationStructure, Laboratory


class TestCaseBase(TestCase):
    fixtures = ["gtapi_data.json"]

    def setUp(self):
        super().setUp()

        # ORG
        self.org1 = OrganizationStructure.objects.filter(name="Organization 1").first()
        self.org2 = OrganizationStructure.objects.filter(name="Organization 2").first()

        # USER
        self.user1 = get_user_model().objects.filter(username="user1").first()
        self.user2 = get_user_model().objects.filter(username="user2").first()
        self.user3 = get_user_model().objects.filter(username="user3").first()
        self.user4 = get_user_model().objects.filter(username="user4").first()

        # PROFILE
        self.profile1 = self.user1.profile
        self.profile2 = self.user2.profile

        # ORGS BY USER
        self.user1_org1_list = OrganizationStructure.os_manager.filter_organization_by_user(
            self.user1).distinct()
        self.user2_org2_list = OrganizationStructure.os_manager.filter_organization_by_user(
            self.user2).distinct()

        # LABS
        self.lab1_org1 = Laboratory.objects.get(name="Lab 1")
        self.lab2_org2 = Laboratory.objects.get(name="Lab 2")
        self.lab3_org2 = Laboratory.objects.get(name="Lab 3")

        # INITIAL DATA

        self.lab_contenttype = ContentType.objects.filter(app_label='laboratory',
                                                          model='laboratory').first()
        self.org_contenttype = ContentType.objects.filter(app_label='laboratory',
                                                          model='organizationstructure').first()

        self.client1 = Client()
        self.client2 = Client()
        self.client3 = Client()
        self.client4 = Client()
        self.client1.force_login(self.user1)
        self.client2.force_login(self.user2)
        self.client3.force_login(self.user3)
        self.client4.force_login(self.user4)
