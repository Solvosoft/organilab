from django.contrib.auth.models import User, Group
from django.urls import reverse

from laboratory.models import PrincipalTechnician, Laboratory
from laboratory.test.utils import OrganizationalStructureDataMixin
from laboratory.views.organizations import OrganizationReportView
from django.test import TestCase, RequestFactory
from constance import config


class OrganizationReportViewTestCase(OrganizationalStructureDataMixin,TestCase):
    """
        This is the test for OrganizationReportView class-based view
    """

    def setUp(self):
        super(OrganizationReportViewTestCase, self).setUp()
        self.factory = RequestFactory()

    def test_group_admin_can_see_organization_report(self):
        """
            'laboratory.view_report' permission is required to see this report
            The laboratory administrator's group (GROUP_ADMIN) has this permission.
        """
        # case A: principal technician in charge of laboratory 1
        lab_pk = self.lab6.id
        request = self.factory.get(f"/lab/{lab_pk}/organizations/reports/list")
        request.user = self.uschi1
        self.assertTrue(self.uroot.has_perm('laboratory.view_report'))
        response = OrganizationReportView.as_view()(request, lab_pk=lab_pk)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(PrincipalTechnician.objects.get(
            credentials__id=self.uschi1.pk, assigned__id=lab_pk))  # one lab can be manage for many principals


    def test_redirect_unathorization_groups(self):
        """
            'laboratory.view_report' permission belongs to GROUP_ADMIN.
            For groups Laboratorist and student the resource must be restricted.
        """
        # laboratorist must not have this permission
        pk = self.lab1.id
        request = self.factory.get(f"/lab/{pk}/organizations/reports/list")
        request.user = self.user_lab_1
        self.assertFalse(self.user_lab_1.has_perm('laboratory.view_report'))
        response = OrganizationReportView.as_view()(request, lab_pk=pk)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("permission_denied"))

        # student neither
        request.user = self.user_est_1
        self.assertFalse(self.user_est_1.has_perm('laboratory.view_report'))
        response = OrganizationReportView.as_view()(request, lab_pk=pk)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("permission_denied"))

