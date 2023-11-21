from django.test import TestCase, Client

from django.contrib.auth import get_user_model

from laboratory.models import OrganizationStructure


class TestCaseBase(TestCase):
    fixtures = ["groups/group.json"]

    def setUp(self):
        super().setUp()
        self.org1 = OrganizationStructure.objects.filter(name="Organization 1").first()
        self.org2 = OrganizationStructure.objects.filter(name="Organization 2").first()
        self.user1 = get_user_model().objects.filter(username="user1").first()
        self.user3 = get_user_model().objects.filter(username="user3").first()
        self.client = Client()
        self.client.force_login(self.user1)
        self.org = self.org1
        self.user = self.user1
