from django.test import TestCase
from django.urls import reverse

from laboratory.models import LaboratoryRoom, Furniture, Catalog
from laboratory.test.utils import OrganizationalStructureDataMixin as OrganizationalStructureData


class ShelfObjectViewTestCases(TestCase):

    def setUp(self):
        self.infrastructure = OrganizationalStructureData()
        self.infrastructure.setUp()

        self.room_lab6 = LaboratoryRoom.objects.create(name="Laboratorio alfa")

        self.infrastructure.lab6.rooms.add(self.room_lab6)
        self.infrastructure.lab6.save()

        self.furniture_lab6 = Furniture.objects.create(
            labroom=self.room_lab6,
            name="Mueble X",
            type=Catalog.objects.filter(key="furniture_type", description="Estante").first()
        )

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

    def test_get_shelf_object_form_lab_group_allowed(self):
        """
            laboratory's group must be the only one
            who can access this creation form
        """
        url = reverse("laboratory:shelfobject_create", kwargs={"lab_pk": self.infrastructure.lab6.pk})
        self.client.force_login(self.laboratorist_user)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")