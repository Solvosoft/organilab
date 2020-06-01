from django.test import TestCase

from laboratory.test.utils import OrganizationalStructureDataMixin


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
        pk_organization = 0
        path = f"/lab/{pk_organization}/organizations/reports/organization"

        pk = self.root_organization.id
        request = self.factory.get(f"/lab/{pk}/organizations/reports/list")
        request.user = self.user_admin
        self.assertTrue(self.user_admin.has_perm('laboratory.view_report'))
        response = OrganizationReportView.as_view()(request, lab_pk=pk)
        self.assertEqual(response.status_code, 200)
