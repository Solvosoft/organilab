from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode

from laboratory.models import Furniture, Catalog, LaboratoryRoom, Shelf
from laboratory.test.utils import OrganizationalStructureDataMixin as OrganizationalStructureData


class ShelfViewTestCases(TestCase):

    def setUp(self):
        infrastructure = OrganizationalStructureData()
        infrastructure.setUp()

        self.lab1 = infrastructure.lab1
        self.lab6 = infrastructure.lab6

        self.room = LaboratoryRoom.objects.create(name="Laboratorio alfa")

        self.lab6.rooms.add(self.room)
        self.lab6.save()

        self.furniture = Furniture.objects.create(
            labroom=self.room,
            name="Mueble X",
            type=Catalog.objects.filter(key="furniture_type", description="Estante").first()
        )

        self.student_user = infrastructure.usch4
        self.laboratorist_user = infrastructure.usch6_i1
        self.professor_user = infrastructure.uschi1
        self.root_user = infrastructure.uroot


    def test_user_has_permission(self):
        """
            showing the user permissions
            permissions: laboratory.add_shelf and laboratory.change_shelf
            groups                       they have these permission
                Student                      no
                Laboratory Administrator     no
                Professor                    yes
        """
        # laboratory.add_shelf
        self.assertFalse(self.student_user.has_perm('laboratory.add_shelf'))
        self.assertFalse(self.laboratorist_user.has_perm('laboratory.add_shelf'))
        self.assertTrue(self.professor_user.has_perm('laboratory.add_shelf'))

        self.assertTrue(self.root_user.has_perm('laboratory.add_shelf'))

        # laboratory.change_shelf
        self.assertFalse(self.student_user.has_perm('laboratory.change_shelf'))
        self.assertFalse(self.laboratorist_user.has_perm('laboratory.change_shelf'))
        self.assertTrue(self.professor_user.has_perm('laboratory.change_shelf'))

        self.assertTrue(self.root_user.has_perm('laboratory.change_shelf'))

    def test_get_shelf_form_laboratorists_group_restricted(self):
        """
            assuming that the previous test is ok
            the laboratorist's group must be restricted
        """
        url = reverse("laboratory:shelf_create", kwargs={"lab_pk": self.lab6.pk})
        data = {"row": 0, "col": 0, "furniture": self.furniture.id}
        self.client.force_login(self.laboratorist_user)
        response = self.client.get(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.laboratorist_user.has_perm('laboratory.add_shelf'))

    def test_get_shelf_form_student_group_restricted(self):
        """
            students must be redirected to the permission denied page
        """
        url = reverse("laboratory:shelf_create", kwargs={"lab_pk": self.lab6.pk})
        data = {"row": 0, "col": 0, "furniture": self.furniture.id}
        self.client.force_login(self.student_user)
        response = self.client.get(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertRedirects(response, reverse('permission_denied'), 302, 200)

    def test_get_shelf_form_professors_group_allowed(self):
        """
             professors are allowed to get this form
        """
        url = reverse("laboratory:shelf_create", kwargs={"lab_pk": self.lab6.pk})
        data = {"row": 0, "col": 0, "furniture": self.furniture.id}
        self.client.force_login(self.professor_user)
        response = self.client.get(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")

    def test_professor_create_shelf(self):
        """
            POST method create a new shelf
        """
        shelf_name = "Gaveta A"
        url = reverse("laboratory:shelf_create", kwargs={"lab_pk": self.lab6.pk})
        data = {
            "row": 0,
            "col": 0,
            "furniture": self.furniture.id,
            "name": shelf_name,
            "type": Catalog.objects.filter(description="Gaveta").first().pk
        }
        self.client.force_login(self.professor_user)
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Shelf.objects.all().first().name, shelf_name)

    def test_professor_can_not_create_shelf(self):
        """
            if the professor try to create a shelf in other lab
            in which he is now allocated he must be restricted
        """
        shelf_name = "Gaveta A"
        url = reverse("laboratory:shelf_create", kwargs={"lab_pk": self.lab1.pk})
        data = {
            "row": 0,
            "col": 0,
            "furniture": self.furniture.id,
            "name": shelf_name,
            "type": Catalog.objects.filter(description="Gaveta").first().pk
        }
        self.client.force_login(self.professor_user)
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertRedirects(response, reverse('permission_denied'), 302, 200)
        self.assertEqual(Shelf.objects.all().count(), 0)

    def test_get_shelf_form_professor_restricted(self):
        """
            the professor is restricted to labs in wich he is not allocated
        """
        url = reverse("laboratory:shelf_create", kwargs={"lab_pk": self.lab1.pk})
        data = {"row": 0, "col": 0, "furniture": self.furniture.id}
        self.client.force_login(self.professor_user)
        response = self.client.get(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertRedirects(response, reverse('permission_denied'), 302, 200)
        self.assertEqual(Shelf.objects.all().count(), 0)

    def test_student_can_not_create_shelf(self):
        """
            the student doesn't have privilege to create a shelf
        """
        shelf_name = "Gaveta A"
        url = reverse("laboratory:shelf_create", kwargs={"lab_pk": self.lab1.pk})
        data = {
            "row": 0,
            "col": 0,
            "furniture": self.furniture.id,
            "name": shelf_name,
            "type": Catalog.objects.filter(description="Gaveta").first().pk
        }
        self.client.force_login(self.student_user)
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertRedirects(response, reverse('permission_denied'), 302, 200)
        self.assertEqual(Shelf.objects.all().count(), 0)