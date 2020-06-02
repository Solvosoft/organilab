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

    def test_user_admin_can_see_organization_report(self):
        """
            'laboratory.view_report' permission is required to see this report
            The laboratory administrator's group (GROUP_ADMIN_PK) has this permission.
        """
        # base case: a principal technician in charge of laboratory 1
        pk = self.lab1.id
        request = self.factory.get(f"/lab/{pk}/organizations/reports/list")
        request.user = self.uroot
        self.assertTrue(self.uroot.has_perm('laboratory.view_report'))
        response = OrganizationReportView.as_view()(request, lab_pk=pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(pk, PrincipalTechnician.objects.get(pk=self.uroot.pk).assigned.pk) #principal manage many labs

        # laboratorist must not have this permission
        #request.user = self.user_laboratoris
        #self.assertFalse(self.user_laboratoris.has_perm('laboratory.view_report'))
        #response = OrganizationReportView.as_view()(request, lab_pk=pk)
        #self.assertEqual(response.status_code, 302)
        #self.assertEqual(response.url, reverse("permission_denied"))

        # student neither
        #request.user = self.user_student
        #self.assertFalse(self.user_student.has_perm('laboratory.view_report'))
        #response = OrganizationReportView.as_view()(request, lab_pk=pk)
        #self.assertEqual(response.status_code, 302)
        #self.assertEqual(response.url, reverse("permission_denied"))

