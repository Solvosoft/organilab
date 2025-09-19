from django.contrib.auth.models import Group
from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from auth_and_perms.tests.base_manage_profile_groups import TestCaseBase
import json


class TestUserProfile(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("auth_and_perms:api_update_groups_by_profile")

    def test_update_profile(self):
        data = {"profile": 1, "groups": [1, 2, 3], "organization": self.org.pk}

        response = self.client.post(
            self.url, data=data, content_type="application/json"
        )
        self.assertTrue(response.status_code == 200)
        user = get_user_model().objects.filter(username="user1").first()
        msg = json.loads(response.content)["detail"]
        self.assertTrue(user.groups.count() == 3)
        self.assertTrue(msg == "Profile was updated successfully.")

    def test_update_profile_no_profile(self):
        data = {"groups": [1, 2, 3], "organization": self.org.pk}
        response = self.client.post(
            self.url, data=data, content_type="application/json"
        )
        self.assertTrue(response.status_code == 400)
        user = get_user_model().objects.filter(username="user1").first()
        msg = json.loads(response.content)["errors"]
        self.assertTrue(user.groups.count() == 0)
        self.assertTrue(msg["profile"][0] == "This field is required.")

    def test_update_profile_wrong_org(self):
        data = {"profile": 1, "groups": [1, 2, 3], "organization": 2}
        response = self.client.post(
            self.url, data=data, content_type="application/json"
        )
        self.assertTrue(response.status_code == 403)
        user = get_user_model().objects.filter(username="user1").first()
        msg = json.loads(response.content)["detail"]
        self.assertTrue(user.groups.count() == 0)
        self.assertTrue(msg == "You do not have permission to perform this action.")

    def test_update_profile_no_org(self):
        data = {"profile": 1, "groups": [1, 2, 3]}
        response = self.client.post(
            self.url, data=data, content_type="application/json"
        )
        self.assertTrue(response.status_code == 404)
        user = get_user_model().objects.filter(username="user1").first()
        msg = json.loads(response.content)["detail"]
        self.assertTrue(msg == "Not found.")
        self.assertTrue(user.groups.count() == 0)

    def test_update_profile_no_login(self):
        self.client.logout()
        data = {"profile": 1, "groups": [1, 2, 3], "organization": 2}
        response = self.client.post(
            self.url, data=data, content_type="application/json"
        )
        self.assertTrue(response.status_code == 403)
        user = get_user_model().objects.filter(username="user1").first()
        self.assertTrue(user.groups.count() == 0)
        msg = json.loads(response.content)["detail"]
        self.assertTrue(user.groups.count() == 0)
        self.assertTrue(msg == "You do not have permission to perform this action.")

    def test_update_profile_new_group(self):
        data = {"profile": 1, "groups": [1, 2, 3, 5], "organization": 1}
        groups = Group.objects.filter(pk__in=[1, 4])
        self.user1.groups.add(*groups)
        response = self.client.post(
            self.url, data=data, content_type="application/json"
        )
        self.assertTrue(response.status_code == 200)
        user = get_user_model().objects.filter(username="user1").first()
        self.assertFalse(user.groups.filter(pk=4).exists())
        msg = json.loads(response.content)["detail"]
        self.assertTrue(user.groups.count() == 4)
        self.assertTrue(msg == "Profile was updated successfully.")

    def test_profile_user_no_profile(self):
        self.client.logout()
        self.client.force_login(self.user3)
        data = {"profile": 1, "groups": [1, 2, 3, 5], "organization": 1}
        groups = Group.objects.filter(pk__in=[1, 4])
        self.user1.groups.add(*groups)
        response = self.client.post(
            self.url, data=data, content_type="application/json"
        )

        self.assertTrue(response.status_code == 404)

    def test_update_profile_empty_group(self):
        data = {"profile": 1, "groups": [], "organization": 1}
        groups = Group.objects.filter(pk__in=[1, 4])
        self.user1.groups.add(*groups)
        response = self.client.post(
            self.url, data=data, content_type="application/json"
        )
        self.assertTrue(response.status_code == 200)
        user = get_user_model().objects.filter(username="user1").first()
        self.assertFalse(user.groups.filter(pk=4).exists())
        msg = json.loads(response.content)["detail"]
        self.assertTrue(user.groups.count() == 0)
        self.assertTrue(msg == "Profile was updated successfully.")

    def test_update_profile_no_group(self):
        data = {"profile": 1, "organization": 1}
        groups = Group.objects.filter(pk__in=[1, 4])
        self.user1.groups.add(*groups)
        response = self.client.post(
            self.url, data=data, content_type="application/json"
        )
        self.assertTrue(response.status_code == 200)
        user = get_user_model().objects.filter(username="user1").first()
        self.assertFalse(user.groups.filter(pk=4).exists())
        msg = json.loads(response.content)["detail"]
        self.assertTrue(user.groups.count() == 0)
        self.assertTrue(msg == "Profile was updated successfully.")

    def test_update_profile_group_str(self):
        data = {"profile": 1, "groups": ["sfa", 4], "organization": 1}
        groups = Group.objects.filter(pk__in=[1, 4])
        self.user1.groups.add(*groups)
        response = self.client.post(
            self.url, data=data, content_type="application/json"
        )

        self.assertTrue(response.status_code == 400)
        user = get_user_model().objects.filter(username="user1").first()
        self.assertFalse(user.groups.count() == 0)
        msg = json.loads(response.content)["errors"]["groups"][0]
        self.assertTrue(msg == "Incorrect type. Expected pk value, received str.")

    def test_update_profile_str(self):
        data = {"profile": "fasga", "groups": ["sfa", 4], "organization": 1}
        groups = Group.objects.filter(pk__in=[1, 4])
        self.user1.groups.add(*groups)
        response = self.client.post(
            self.url, data=data, content_type="application/json"
        )

        self.assertTrue(response.status_code == 400)
        user = get_user_model().objects.filter(username="user1").first()
        self.assertFalse(user.groups.count() == 0)
        msg = json.loads(response.content)["errors"]["profile"][0]
        self.assertTrue(msg == "Incorrect type. Expected pk value, received str.")

    def test_update_profile_unknwon_profile(self):
        data = {"profile": 1848464863, "groups": [4], "organization": 1}
        groups = Group.objects.filter(pk__in=[1, 4])
        self.user1.groups.add(*groups)
        response = self.client.post(
            self.url, data=data, content_type="application/json"
        )

        self.assertTrue(response.status_code == 400)
        user = get_user_model().objects.filter(username="user1").first()
        self.assertFalse(user.groups.count() == 0)
        msg = json.loads(response.content)["errors"]["profile"][0]
        self.assertTrue(msg == f'Invalid pk "1848464863" - object does not exist.')

    def test_update_profile_unknwon_group(self):
        data = {"profile": 1, "groups": [5994686], "organization": 1}
        groups = Group.objects.filter(pk__in=[1, 4])
        self.user1.groups.add(*groups)
        response = self.client.post(
            self.url, data=data, content_type="application/json"
        )

        self.assertTrue(response.status_code == 400)
        user = get_user_model().objects.filter(username="user1").first()
        self.assertFalse(user.groups.count() == 0)
        msg = json.loads(response.content)["errors"]["groups"][0]
        self.assertTrue(msg == f'Invalid pk "5994686" - object does not exist.')

    def test_update_profile_unknwon_org(self):
        data = {"profile": 1, "groups": [4], "organization": 3138346384}
        groups = Group.objects.filter(pk__in=[1, 4])
        self.user1.groups.add(*groups)
        response = self.client.post(
            self.url, data=data, content_type="application/json"
        )
        self.assertTrue(response.status_code == 404)
        user = get_user_model().objects.filter(username="user1").first()
        self.assertFalse(user.groups.count() == 0)
        msg = json.loads(response.content)["detail"]
        self.assertTrue(msg == "Not found.")
