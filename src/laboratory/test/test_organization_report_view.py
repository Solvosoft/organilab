import json
import random
from django.contrib.auth.models import Group
from constance import config
from django.urls import reverse
from laboratory.models import PrincipalTechnician, OrganizationStructure, Laboratory
from laboratory.test.utils import OrganizationalStructureDataMixin
from laboratory.views.organizations import OrganizationReportView
from django.test import TestCase, RequestFactory


class OrganizationReportViewTestCase(OrganizationalStructureDataMixin, TestCase):
    """
        This is the test for OrganizationReportView class-based view.

                    This is the organization structure
                        -------------------------
                        |          root         |         * = GROUP_STUDENT
                        -------------------------
                        /             |         \
                      dep1           dep2       dep3       GROUP_ADMIN
                   /   \    \      /    \        |  \
                sch1     sch2  sch3    sch4   sch5   sch6  GROUP_LABORATORIST
                /  \      |     |     / |       |      |
              lab1 lab2  lab3  lab4  /isch1    lab8   lab9
                                   lab5 / \
                                     lab6 lab7

        Here we are going to test the access level for the different nodes of the tree in order to reach a resource.
        To see the organization report of the specific lab, the user must have 'laboratory.view_report' permission and
        the only group that have this permission is the admin's group.

        Image that represents the data of the relationship between users, principals and the organization structure
        see: https://user-images.githubusercontent.com/20632410/83577403-4f232b80-a4f1-11ea-85da-ea24228eea4f.png
    """

    def setUp(self):
        super(OrganizationReportViewTestCase, self).setUp()
        self.factory = RequestFactory()

        # extra case
        # principal who manage labs from other school
        for i, org, lab in [(1, self.school1, self.lab1),
                            (2, self.school1, self.lab2),
                            ]:
            usch6_i1 = PrincipalTechnician.objects.create(
                name="Keylor Vargas " + str(i),
                phone_number="88-0000-" + str(random.randint(1000, 9999)),
                id_card="8-%d-7890" % (random.randint(1000, 9999)),
                email="usch6_i1@organilab.org",
                organization=org,
                assigned=lab
            )
            usch6_i1.credentials.add(self.usch6_i1)

        gpa = Group.objects.get(pk=config.GROUP_ADMIN_PK)
        self.usch6_i1.groups.add(gpa)

    def test_user_root_can_see_all_the_organization_laboratories_report(self):
        """
            User root belongs to admin's group, is a Principal Technician and is assigned to the root of the
            organization structure. He is the only one who can see the entire organization labs reports.

            Testing 'GET' method.
        """

        lab_pk = self.lab6.id
        request = self.factory.get(f"/lab/{lab_pk}/organizations/reports/list")
        request.user = self.uroot
        self.assertTrue(self.uroot.has_perm('laboratory.view_report'))
        response = OrganizationReportView.as_view()(request, lab_pk=lab_pk)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(PrincipalTechnician.objects.filter(
            credentials__id=self.uroot.pk, organization__id=self.root.pk).first())
        self.assertEqual(response.context_data["object_list"].count(), Laboratory.objects.all().count(),
                         msg=f"user root can see all labs")

    def test_user_principal_admin_can_see_organization_report_of_the_allocated_labs(self):
        """
            A Principal that is not a root is supposed to see only the allocated labs.

            Testing 'GET' method.
        """
        # first case:
        #   PricipalTechnician: puschi1
        #   User: uschi1
        #   Group: GROUP_ADMIN
        #   school: isch1
        #   labs: 6,7
        allocated_labs = [p.assigned.name for p in PrincipalTechnician.objects.filter(credentials__id=self.uschi1.pk)]

        lab_pk = self.lab6.id
        request = self.factory.get(f"/lab/{lab_pk}/organizations/reports/list")
        request.user = self.uschi1
        self.assertTrue(self.uschi1.has_perm('laboratory.view_report'))
        response = OrganizationReportView.as_view()(request, lab_pk=lab_pk)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(PrincipalTechnician.objects.filter(credentials__id=self.uschi1.pk, assigned__id=lab_pk).first())
        self.assertEqual(response.context_data["object_list"].count(), len(allocated_labs))
        lab_names = [*map(lambda lab: lab.name, response.context_data["object_list"])]

        self.assertListEqual(lab_names, allocated_labs)

        # second case:
        #   the user try to access a lab from other school in which he doesn't have permissions
        #   the resource must be restricted and the user must be redirected
        lab_pk = self.lab1.id # other lab
        request = self.factory.get(f"/lab/{lab_pk}/organizations/reports/list")
        request.user = self.uschi1
        self.assertTrue(self.uschi1.has_perm('laboratory.view_report'))
        response = OrganizationReportView.as_view()(request, lab_pk=lab_pk)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("permission_denied"))

    def test_principal_can_see_just_assigned_labs_after_apply_filter(self):
        """
            Testing 'POST' method. This method was use to perform the report filter.
            In the first case the user must be able to see report from allocated labs.
            In the second case the user must be restricted as he doesn't have permission in other school labs.
        """
        # first case:
        #   PricipalTechnician: puschi1
        #   User: uschi1
        #   Group: GROUP_ADMIN
        #   school: isch1
        #   labs: 6,7
        allocated_labs = [p.assigned.name for p in PrincipalTechnician.objects.filter(credentials__id=self.uschi1.pk)]

        lab_pk = self.lab6.id
        data = {"filter_organization": OrganizationStructure.objects.filter(name="Inter School 1").first().pk}
        request = self.factory.post(f"/lab/{lab_pk}/organizations/reports/list", data)
        request.user = self.uschi1
        self.assertTrue(self.uschi1.has_perm('laboratory.view_report'))
        response = OrganizationReportView.as_view()(request, lab_pk=lab_pk)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(len(PrincipalTechnician.objects.filter(credentials__id=self.uschi1.pk)), 0)
        self.assertEqual(response.context_data["object_list"].count(), len(allocated_labs))
        lab_names = [*map(lambda lab: lab.name, response.context_data["object_list"])]
        self.assertTrue(all([True if name in allocated_labs else False for name in lab_names]))

        # this case must return 0, as the principal is not allocated to School 6 or any lab there
        lab_pk = self.lab6.id
        data = {"filter_organization": OrganizationStructure.objects.filter(name="School 6").first().pk} # this can be a weird case as the principal is not able to chose organization structure that are not allocated to him
        request = self.factory.post(f"/lab/{lab_pk}/organizations/reports/list", data)
        request.user = self.uschi1
        self.assertTrue(self.uschi1.has_perm('laboratory.view_report'))
        response = OrganizationReportView.as_view()(request, lab_pk=lab_pk)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(PrincipalTechnician.objects.filter(
            credentials__id=self.uschi1.pk, assigned__id=lab_pk).count(), 0)
        self.assertEqual(response.context_data["object_list"].count(), 0,
                         msg=f"must return 0 and return {response.context_data['object_list']}") #### aunque retorne los labs asignados, no deberia devolver nada, ya que permite a un tercero saber a que departamento esta asignado el usuario

    def test_principal_apply_filter_for_one_of_two_schools(self):
        """
            This case occurs when a Principal is allocated to different labs in different schools so, if the filter is
            performed it must return specific school labs report
        """
        # extra case:
        # labs: 1,2, 6,7, 9
        # schools: 1, i, 6
        # filtering by 'School 1' must return  2 labs, lab1 and lab2
        allocated_labs = [p.assigned.name for p in PrincipalTechnician.objects.filter(credentials__id=self.usch6_i1.pk)]

        lab_pk = self.lab6.id
        data = {"filter_organization": OrganizationStructure.objects.filter(name="School 1").first().pk}  # this can be a weird case as the principal is not able to chose organization structure that are not allocated to him
        request = self.factory.post(f"/lab/{lab_pk}/organizations/reports/list", data)
        request.user = self.usch6_i1
        self.assertTrue(self.usch6_i1.has_perm('laboratory.view_report'))
        response = OrganizationReportView.as_view()(request, lab_pk=lab_pk)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(len(allocated_labs), 0)
        amount_labs_response = response.context_data["object_list"].count()
        names_labs_response = [lab.name for lab in response.context_data["object_list"]]
        self.assertEqual(amount_labs_response, 2)
        self.assertNotEqual(amount_labs_response, len(allocated_labs))
        self.assertListEqual(names_labs_response, ["Laboratory 2", "Laboratory 1"])

    def test_root_user_can_apply_filters_for_each_school(self):
        """
            Testing 'POST' method.
            Root user has the permission to apply filters for any school.

            data:
                PricipalTechnician: pturoot
                User: uroot
                Group: GROUP_ADMIN
                school/Dep: root
                labs: must be able to see all the labs, they are nine
        """

        # case one: School 1, return lab 1 and 2
        self._check_case_schools_labs("School 1", ["Laboratory 1", "Laboratory 2"])

        # case two: School 2, return lab 3 and 4
        self._check_case_schools_labs("School 2", ["Laboratory 3"])

        # case three: School 3, return lab 4
        self._check_case_schools_labs("School 3", ["Laboratory 4"])

        # case four: School 4, return lab 5, 6 and 7
        self._check_case_schools_labs("School 4",  ["Laboratory 5", "Laboratory 6", "Laboratory 7"])

        # case five: School 4, return lab 5, 6 and 7
        self._check_case_schools_labs("Inter School 1", ["Laboratory 6", "Laboratory 7"])

        # case six: School 5, return lab 8
        self._check_case_schools_labs("School 5",  ["Laboratory 8"])

        # case seven: School 6, return lab 9
        self._check_case_schools_labs("School 6", ["Laboratory 9"])

    def _check_case_schools_labs(self, school, labs):
        lab_pk = self.lab1.id
        data = {"filter_organization": OrganizationStructure.objects.filter(name=school).first().pk}
        request = self.factory.post(f"/lab/{lab_pk}/organizations/reports/list", data)
        request.user = self.uroot
        self.assertTrue(self.uroot.has_perm('laboratory.view_report'))
        response = OrganizationReportView.as_view()(request, lab_pk=lab_pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["object_list"].count(), len(labs),
                         msg=f"{school} is suppose to return {labs} and return:{response.context_data['object_list']}")
        lab_names = [*map(lambda lab:lab.name, response.context_data["object_list"])]

        self.assertTrue(all([True if name in labs else False for name in lab_names]))

    def test_redirect_user_if_does_not_belong_to_admins_group(self):
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
