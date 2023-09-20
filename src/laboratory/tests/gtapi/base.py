import json
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, Client
from django.urls import reverse

from auth_and_perms.organization_utils import organization_can_change_laboratory
from laboratory.models import OrganizationStructure, Laboratory, Furniture, ShelfObject
from laboratory.utils import check_user_access_kwargs_org_lab


class TestCaseBase(TestCase):

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
        self.profile3 = self.user3.profile
        self.profile4 = self.user4.profile

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

        #DEFAULT DATA
        self.lab = self.lab1_org1
        self.org = self.org1
        self.user = self.user1
        self.client = self.client1


    def check_tests(self, response, status_code, org_can_change, user_access, results_data=True):
        results = []

        self.assertEqual(response.status_code, status_code)

        has_permission = organization_can_change_laboratory(self.lab, self.org)
        check_user_access = check_user_access_kwargs_org_lab(self.org.pk,
                                                             self.lab.pk, self.user)
        self.assertEqual(has_permission, org_can_change)
        self.assertEqual(check_user_access, user_access)

        if response.content:
            response_data = json.loads(response.content)
            self.assertEqual("results" not in response_data, results_data)

            if not results_data:
                results = response_data["results"]

        return results


class ShelfViewTest(TestCaseBase):
    fixtures = ["gtapi/gtapi_shelf_data.json"]

    def setUp(self):
        super().setUp()
        self.furniture = Furniture.objects.get(pk=1)
        self.shelfobject = ShelfObject.objects.get(pk=1)
        self.url = reverse("shelf-list")
        self.data = {
            "shelfobject": self.shelfobject.pk,
            "relfield": self.furniture.pk,
            "page": 1,
            "laboratory": self.lab.pk,
            "organization": self.org.pk
        }

class FurnitureTestCaseBase(TestCaseBase):
    fixtures = ["gtapi/gtapi_furniture_data.json"]

    def setUp(self):
        super().setUp()
