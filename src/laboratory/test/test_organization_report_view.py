from laboratory.models import PrincipalTechnician
from laboratory.test.utils import OrganizationalStructureDataMixin
from laboratory.views.organizations import OrganizationReportView
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.auth.models import User, Group
from django.test import TestCase, RequestFactory
from constance import config



class OrganizationReportViewTestCase(OrganizationalStructureDataMixin,TestCase):

    USER_ADMIN = "user_admin"
    USER_LABORATORIST = "user_laboratoris"
    USER_STUDENT = "user_student"

    PASSWORD = "abcd"

    def setUp(self):
        super(OrganizationReportViewTestCase, self).setUp()

        self.user_admin = User.objects.create_user(
            self.USER_ADMIN,
            "admin@organillab.org",
            self.PASSWORD
        )
        self.user_laboratoris = User.objects.create_user(
            self.USER_LABORATORIST,
            "laboratoris@organillab.org",
            self.PASSWORD
        )
        self.user_student = User.objects.create_user(
            self.USER_STUDENT,
            "student@organillab.org",
            self.PASSWORD
        )

        admin_group = Group.objects.get(pk=config.GROUP_ADMIN_PK)
        laboratoris_group = Group.objects.get(pk=config.GROUP_LABORATORIST_PK)
        student_group = Group.objects.get(pk=config.GROUP_STUDENT_PK)

        self.user_admin.groups.add(admin_group)
        self.user_laboratoris.groups.add(laboratoris_group)
        self.user_student.groups.add(student_group)

        self.factory = RequestFactory()


        pt = PrincipalTechnician(name=self.user_admin.first_name + " " + self.user_admin.last_name,
                                 phone_number="8888-8888",
                                 id_card="0-0000-0000",
                                 email=self.user_admin.email,
                                 organization=self.root_organization
        )

        pt.save()
        pt.credentials.add(self.user_admin)

        self.user_admin.groups.add(admin_group)

        self.user_admin.save()


    def test_user_admin_can_see_list(self):
        pk = self.root_organization.id
        request = self.factory.get(f"/lab/{pk}/organizations/reports/list")
        request.user = self.user_admin

        response = OrganizationReportView.as_view()(request)

        self.assertEqual(response.status_code, 200)

