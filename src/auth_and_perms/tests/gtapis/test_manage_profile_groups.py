from django.contrib.auth.models import Group, User
from django.urls import reverse

from auth_and_perms.tests.base_manage_profile_groups import TestCaseBase
import json

class TestUserProfile(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("groupsbyprofile-list")
        groups = Group.objects.filter(pk__in=[1, 4])
        self.user1.groups.add(*groups)

    def test_get_profile_group(self):
        response = self.client.get(f'{self.url}?profile={self.user.pk}')
        result = [id['id'] for id in json.loads(response.content)['results']]
        self.assertTrue(response.status_code==200)
        total = json.loads(response.content)['total_count']
        self.assertTrue(self.user.groups.filter(pk__in=result).count()==total)

    def test_get_profile_group_no_login(self):
        self.client.logout()
        response = self.client.get(f'{self.url}?profile={self.user.pk}')
        self.assertNotIn('result',json.loads(response.content))
        self.assertTrue(response.status_code==403)
        self.assertTrue(self.user.groups.count()==2)
        msg = json.loads(response.content)['detail']
        self.assertTrue(msg=="Authentication credentials were not provided.")

    def test_get_profile_group_no_profile(self):
        response = self.client.get(f'{self.url}')
        self.assertNotIn('result',json.loads(response.content))
        self.assertTrue(response.status_code==400)
        self.assertTrue(self.user.groups.count()==2)
        msg = json.loads(response.content)['errors']
        self.assertTrue(msg['profile'][0]=="This field is required.")

    def test_get_profile_group_no_groups(self):
        response = self.client.get(f'{self.url}?profile={self.user3.pk}')
        self.assertTrue(json.loads(response.content)['results']==[])
        self.assertTrue(json.loads(response.content)['total_count']==0)
        self.assertTrue(response.status_code==200)
        self.assertTrue(self.user3.groups.count()==0)

    def test_get_profile_group_str_profile(self):
        response = self.client.get(f'{self.url}?profile=sss')
        self.assertTrue(response.status_code==400)
        msg = json.loads(response.content)['errors']['profile'][0]
        self.assertTrue(msg == "Incorrect type. Expected pk value, received str.")

    def test_get_profile_group_unknwon_profile(self):
        response = self.client.get(f'{self.url}?profile=40000')
        self.assertTrue(response.status_code==400)
        msg = json.loads(response.content)['errors']['profile'][0]
        self.assertTrue(msg == f'Invalid pk "40000" - object does not exist.')
class TestProfileSelect(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("usersbyorg-list")
        groups = Group.objects.filter(pk__in=[1, 4])
        self.user1.groups.add(*groups)

    def test_get_profile_group(self):
        response = self.client.get(f'{self.url}?organization={self.org.pk}')
        result = [id['id'] for id in json.loads(response.content)['results']]
        self.assertTrue(response.status_code==200)
        self.assertTrue(len(result)>0)
        total = json.loads(response.content)['total_count']
        self.assertTrue(self.org.users.count()==total)

    def test_get_profile_group_no_org(self):
        response = self.client.get(f'{self.url}')
        self.assertTrue(response.status_code==400)
        self.assertTrue(json.loads(response.content)['errors']['organization'][0]=='This field is required.')

    def test_get_profile_group_no_login(self):
        self.client.logout()
        response = self.client.get(f'{self.url}?organization={self.org.pk}')
        self.assertTrue(response.status_code==403)
        msg = json.loads(response.content)['detail']
        self.assertTrue(msg == "Authentication credentials were not provided.")

    def test_get_profile_group_str_org(self):
        response = self.client.get(f'{self.url}?organization=sss')
        self.assertTrue(response.status_code==400)
        msg = json.loads(response.content)['errors']['organization'][0]
        self.assertTrue(msg == "Incorrect type. Expected pk value, received str.")

    def test_get_profile_group_unknwon_orge(self):
        response = self.client.get(f'{self.url}?organization=66641')
        self.assertTrue(response.status_code==400)
        msg = json.loads(response.content)['errors']['organization'][0]
        self.assertTrue(msg == f'Invalid pk "66641" - object does not exist.')
