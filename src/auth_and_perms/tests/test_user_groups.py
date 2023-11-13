from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from laboratory.models import OrganizationStructure
import json
class TestCaseBase(TestCase):
    fixtures = ["groups/group.json"]

    def setUp(self):
        super().setUp()
        self.org1 = OrganizationStructure.objects.filter(name="Organization 1").first()
        self.org2 = OrganizationStructure.objects.filter(name="Organization 2").first()
        self.user1 = get_user_model().objects.filter(username="user1").first()
        self.client = Client()
        self.client.force_login(self.user1)
        self.org = self.org1
        self.user = self.user1

class TestUserProfile(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("auth_and_perms:api_update_groups_by_profile")

    def test_update_profile(self):
        data = {"profile": 1,
                "groups":[1,2,3],
                "organization":self.org.pk}

        response = self.client.post(self.url,data=data, content_type='application/json')
        print(response.content)

        self.assertTrue(response.status_code==200)
        user = get_user_model().objects.filter(username="user1").first()
        msg = json.loads(response.content)['detail']
        self.assertTrue(user.groups.count()==3)
        self.assertTrue(msg=='Profile was updated successfully.')

    def test_update_profile_no_profile(self):
        data = {"groups":[1,2,3],
                "organization":self.org.pk}
        response = self.client.post(self.url,data=data, content_type='application/json')
        self.assertTrue(response.status_code==404)
        user = get_user_model().objects.filter(username="user1").first()
        self.assertTrue(user.groups.count()==0)
        print(response.content)

    def test_update_profile_wrong_org(self):
        data = {"profile": 1,
                "groups":[1,2,3],
                "organization":2}
        response = self.client.post(self.url,data=data, content_type='application/json')
        self.assertTrue(response.status_code==403)
        print(response.content)
        user = get_user_model().objects.filter(username="user1").first()
        self.assertTrue(user.groups.count()==0)

    def test_update_profile_no_org(self):
        data = {"profile": 1,
                "groups":[1,2,3]}
        response = self.client.post(self.url,data=data, content_type='application/json')
        self.assertTrue(response.status_code==404)
        user = get_user_model().objects.filter(username="user1").first()
        self.assertTrue(user.groups.count()==0)

    def test_update_profile_no_org(self):
        data = {"profile": 1,
                "groups":[1,2,3]}
        response = self.client.post(self.url,data=data, content_type='application/json')
        self.assertTrue(response.status_code==404)
        user = get_user_model().objects.filter(username="user1").first()
        self.assertTrue(user.groups.count()==0)

