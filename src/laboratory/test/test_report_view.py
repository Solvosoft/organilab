from django.test import TestCase

from laboratory.test.utils import OrganizationalStructureDataMixin
from laboratory.views.reports import report_organization_building


class ReportViewTestCase(OrganizationalStructureDataMixin, TestCase):
    # laboratory.do_report
    #

    # laboratory.do_report
    # /lab/55/organizations/reports/list >> listview

    def setUp(self):
        super(ReportViewTestCase, self).setUp()

    def test_admin_has_autorization_to_see_organization_report(self):
        """
            'laboratory.do_report' permission is required to reach this resource
        """

        pk = self.root_organization.pk
        request = self.factory.get(f"/lab/{pk}/organizations/reports/organization")
        request.user = self.user_admin
        self.assertTrue(self.user_admin.has_perm('laboratory.do_report'))
        response = report_organization_building(request, lab_pk=pk)
        self.assertEqual(response.status_code, 200)

        # laboratorist must not have this permission
        request.user = self.user_laboratoris
        self.assertFalse(self.user_laboratoris.has_perm('laboratory.do_report'))
        response = report_organization_building(request, lab_pk=pk)
        self.assertNotEqual(response.status_code, 200)

        # student neither
        request.user = self.user_student
        self.assertFalse(self.user_student.has_perm('laboratory.do_report'))
        response = report_organization_building(request, lab_pk=pk)
        self.assertNotEqual(response.status_code, 200)
