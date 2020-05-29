from distutils.command.config import config

from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test import Client

class OrganizationReportViewTestCase(TestCase):

    USER_ADMIN = "user_admin"
    USER_LABORATORIST = "user_laboratoris"
    USER_STUDENT = "user_student"

    PASSWORD = "abcd"

    def setUp(self):
        user_admin = User.objects.create_user(self.USER_ADMIN, "admin@organillab.org", self.PASSWORD)
        user_laboratoris = User.objects.create_user(self.USER_LABORATORIST, "laboratoris@organillab.org", self.PASSWORD)
        user_student = User.objects.create_user(self.USER_STUDENT, "student@organillab.org", self.PASSWORD)

        admin_group = Group.objects.get(pk=config.GROUP_ADMIN_PK)
        laboratoris_group = Group.objects.get(pk=config.GROUP_LABORATORIST_PK)
        student_group = Group.objects.get(pk=config.GROUP_STUDENT_PK)

        user_admin.groups.add(admin_group)
        user_laboratoris.groups.add(laboratoris_group)
        user_student.group.add(student_group)

        self.client = Client()



    def test_user_admin_(self):
        credentials = {
            "username": self.USER_ADMIN,
            "password": self.PASSWORD
        }

        response = self.client.post('/accounts/login/', **credentials)
        self.assertTrue(response.context['user'].is_active)
        response = self.client.get('/customer/details/')
        self.assertEqual(response.status_code, 200)


