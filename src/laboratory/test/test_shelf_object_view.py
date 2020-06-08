from django.test import TestCase

from laboratory.models import Object
from laboratory.test.utils import OrganizationalStructureDataMixin as OrganizationalStructureData


class ShelfObjectViewTestCases(TestCase):

    def setUp(self):
        self.infrastructure = OrganizationalStructureData()
        self.infrastructure.setUp()

        self.student_user = self.infrastructure.usch4
        self.laboratorist_user = self.infrastructure.usch6_i1
        self.professor_user = self.infrastructure.uschi1
        self.root_user = self.infrastructure.uroot

    def test_permissions(self):
        """
            The lab's group is the only one that has this three permissions:
            Laboratory: add_shelfobject, change_shelfobject, delete_shelfobject
        """
        # student
        self.assertTrue(self.student_user.has_perm("laboratory.add_shelfobject"))
        self.assertTrue(self.student_user.has_perm("laboratory.change_shelfobject"))
        self.assertTrue(self.student_user.has_perm("laboratory.delete_shelfobject"))

        # laboratoris
        self.assertTrue(self.laboratorist_user.has_perm("laboratory.add_shelfobject"))
        self.assertTrue(self.laboratorist_user.has_perm("laboratory.change_shelfobject"))
        self.assertTrue(self.laboratorist_user.has_perm("laboratory.delete_shelfobject"))

        # professor
        self.assertTrue(self.professor_user.has_perm("laboratory.add_shelfobject"))
        self.assertTrue(self.professor_user.has_perm("laboratory.change_shelfobject"))
        self.assertTrue(self.professor_user.has_perm("laboratory.delete_shelfobject"))

