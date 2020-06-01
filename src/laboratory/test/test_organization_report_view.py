from laboratory.models import PrincipalTechnician
from laboratory.test.utils import OrganizationalStructureDataMixin
from laboratory.views.organizations import OrganizationReportView
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.auth.models import User, Group
from django.test import TestCase, RequestFactory
from constance import config



class OrganizationReportViewTestCase(OrganizationalStructureDataMixin,TestCase):
    """
        This is the test for OrganizationReportView class-based view
    """

    USER_ADMIN = "user_admin"
    USER_LABORATORIST = "user_laboratorist"
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

    def test_user_admin_can_see_organization_report(self):
        """
            'laboratory.view_report' permission is required to see this report
            The laboratory administrator's group (GROUP_ADMIN_PK) has this permission.
        """
        # base case: when everything is ok
        pk = self.root_organization.id
        request = self.factory.get(f"/lab/{pk}/organizations/reports/list")
        request.user = self.user_admin
        self.assertTrue(self.user_admin.has_perm('laboratory.view_report'))
        response = OrganizationReportView.as_view()(request, lab_pk=pk)
        self.assertEqual(response.status_code, 200)

        # laboratorist must not have this permission
        request.user = self.user_laboratoris
        self.assertFalse(self.user_laboratoris.has_perm('laboratory.view_report'))
        response = OrganizationReportView.as_view()(request, lab_pk=pk)
        self.assertNotEqual(response.status_code, 200)

        # student neither
        request.user = self.user_student
        self.assertFalse(self.user_student.has_perm('laboratory.view_report'))
        response = OrganizationReportView.as_view()(request, lab_pk=pk)
        self.assertNotEqual(response.status_code, 200)


"""
    Laboratory Administrator's group (GROUP_ADMIN_PK) have some permissions like:
    
    perms_laboratory = [  
         # reservations
        "add_reservation", "change_reservation", "delete_reservation", "add_reservationtoken",
        "change_reservationtoken", "delete_reservationtoken", "view_reservation",

        # shelf
        "view_shelf", "add_shelf", "change_shelf", "delete_shelf",
        
        # shelfobjets
        "view_shelfobject", "add_shelfobject", "change_shelfobject", "delete_shelfobject",
        
        # objets
        "view_object", "add_object", "change_object", "delete_object",
        
        # objectfeatures
        "view_objectfeatures", "add_objectfeatures", "change_objectfeatures", "delete_objectfeatures",
        
        # procedurerequiredobject
        "view_procedurerequiredobject", "add_procedurerequiredobject", "change_procedurerequiredobject",
        "delete_procedurerequiredobject",
        
        # laboratory
        "view_laboratory", "add_laboratory", "change_laboratory", "delete_laboratory",
        
        # laboratoryroom
        "view_laboratoryroom", "add_laboratoryroom", "change_laboratoryroom", "delete_laboratoryroom",
        
        # furniture
        "view_furniture", "add_furniture", "change_furniture", "delete_furniture",
        
        # Products
        "view_product", "add_product", "change_product", "delete_product",
        # onsertation
        "view_observation", "add_observation", "change_observation", "delete_observation",
        # CL Inventory
        "view_clinventory", "add_clinventory", "change_clinventory", "delete_clinventory", "add_solution",
        # solutions
        "view_solution", "add_solution", "change_solution", "delete_solution",

        # reports
        "view_report", "do_report",
    ]
"""