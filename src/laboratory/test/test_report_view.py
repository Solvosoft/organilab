from django.test import TestCase

from laboratory.test.utils import OrganizationalStructureDataMixin
from laboratory.views.reports import report_organization_building, report_labroom_building, report_shelf_objects, \
    report_limited_shelf_objects


class ReportViewTestCase(OrganizationalStructureDataMixin, TestCase):
    """
        test for report view
    """

    def check_simple_view_if_admin_has_permissions(self, function=None, resource=None, permission=None, pk=None):

        request = self.factory.get(resource)
        request.user = self.user_admin
        self.assertTrue(self.user_admin.has_perm(permission))
        response = function(request, lab_pk=pk)
        self.assertEqual(response.status_code, 200)

        # laboratorist must not have this permission
        request.user = self.user_laboratoris
        self.assertFalse(self.user_laboratoris.has_perm(permission))
        response = function(request, lab_pk=pk)
        self.assertNotEqual(response.status_code, 200)

        # student neither
        request.user = self.user_student
        self.assertFalse(self.user_student.has_perm(permission))
        response = function(request, lab_pk=pk)
        self.assertNotEqual(response.status_code, 200)


    def test_admin_has_autorization_to_see_organization_report(self):
        """
            'laboratory.do_report' permission is required to reach this resource
        """
        pk = self.root_organization.pk
        path = f"/lab/{pk}/organizations/reports/organization"

        self.check_simple_view_if_admin_has_permissions(
            function=report_organization_building,
            resource=path,
            permission='laboratory.do_report',
            pk=pk
        )

    def test_admin_has_authorization_to_see_lab_room_building_report(self):
        """
            'laboratory.do_report' permission is required to reach this resource
        """
        pk = self.root_organization.pk
        path = f"lab/{pk}/reports/laboratory"

        self.check_simple_view_if_admin_has_permissions(
            function=report_labroom_building,
            resource=path,
            permission='laboratory.do_report',
            pk=pk
        )

    def test_admin_has_authorization_to_see_shelf_objects_report(self):
        """
            'laboratory.do_report' permission is required to reach this resource
        """
        pk = self.root_organization.pk
        path = f"lab/{pk}/reports/shelf_objects"

        self.check_simple_view_if_admin_has_permissions(
            function=report_shelf_objects,
            resource=path,
            permission='laboratory.do_report',
            pk=pk
        )

    def test_admin_has_authorization_to_see_limits_shelf_objects_report(self):
        """
            'laboratory.do_report' permission is required to reach this resource
        """
        pk = self.root_organization.pk
        path = f"lab/{pk}/reports/limited_shelf_objects"

        self.check_simple_view_if_admin_has_permissions(
            function=report_limited_shelf_objects,
            resource=path,
            permission='laboratory.do_report',
            pk=pk
        )

