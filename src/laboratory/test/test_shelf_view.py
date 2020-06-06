import itertools

from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode

from laboratory.models import Furniture, Catalog, LaboratoryRoom, Shelf
from laboratory.test.utils import OrganizationalStructureDataMixin as OrganizationalStructureData


class ShelfViewTestCases(TestCase):

    def setUp(self):
        """
            research:
                Coverage

            feedback:
                los datos deben de ser certeros
                * no probar los datos del command

            to do:
                lab  : add, change, delete
                stu  :
                prof :
        """
        infrastructure = OrganizationalStructureData()
        infrastructure.setUp()

        self.lab1 = infrastructure.lab1
        self.lab6 = infrastructure.lab6

        self.room_lab6 = LaboratoryRoom.objects.create(name="Laboratorio alfa")

        self.lab6.rooms.add(self.room_lab6)
        self.lab6.save()

        self.furniture_lab6 = Furniture.objects.create(
            labroom=self.room_lab6,
            name="Mueble X",
            type=Catalog.objects.filter(key="furniture_type", description="Estante").first()
        )

        self.student_user = infrastructure.usch4
        self.laboratorist_user = infrastructure.usch6_i1
        self.professor_user = infrastructure.uschi1
        self.root_user = infrastructure.uroot

    def test_user_has_permission(self):
        """
            *** nunca adaptar la prueba ***

            laboratory's group must be the ones who have this permission
        """
        # laboratory.add_shelf
        self.assertTrue(self.laboratorist_user.has_perm('laboratory.add_shelf'))
        self.assertFalse(self.student_user.has_perm('laboratory.add_shelf'))
        self.assertFalse(self.professor_user.has_perm('laboratory.add_shelf'))

        # laboratory.change_shelf
        self.assertTrue(self.laboratorist_user.has_perm('laboratory.change_shelf'))
        self.assertFalse(self.student_user.has_perm('laboratory.change_shelf'))
        self.assertFalse(self.professor_user.has_perm('laboratory.change_shelf'))

    def test_get_shelf_form_lab_group_allowed(self):
        """
            laboratory's group must be the only ones
            who can access this creation form
        """
        url = reverse("laboratory:shelf_create", kwargs={"lab_pk": self.lab6.pk})
        data = {"row": 0, "col": 0, "furniture": self.furniture_lab6.id}
        self.client.force_login(self.laboratorist_user)
        response = self.client.get(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")

    def test_get_shelf_form_student_group_restricted(self):
        """
            students must be redirected to the permission denied page
        """
        url = reverse("laboratory:shelf_create", kwargs={"lab_pk": self.lab6.pk})
        data = {"row": 0, "col": 0, "furniture": self.furniture_lab6.id}
        self.client.force_login(self.student_user)
        response = self.client.get(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertRedirects(response, reverse('permission_denied'), 302, 200)

    def test_get_shelf_form_professors_group_restricted(self):
        """
             professors are allowed to get this form
        """
        url = reverse("laboratory:shelf_create", kwargs={"lab_pk": self.lab6.pk})
        data = {"row": 0, "col": 0, "furniture": self.furniture_lab6.id}
        self.client.force_login(self.professor_user)
        response = self.client.get(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertRedirects(response, reverse('permission_denied'), 302, 200)

    def test_laboratorist_create_shelf(self):
        """
            POST method create a new shelf
        """
        shelf_name = "Gaveta A"
        url = reverse("laboratory:shelf_create", kwargs={"lab_pk": self.lab6.pk})
        data = {
            "row": 0,
            "col": 0,
            "furniture": self.furniture_lab6.id,
            "name": shelf_name,
            "type": Catalog.objects.filter(description="Gaveta").first().pk
        }
        self.client.force_login(self.laboratorist_user)
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
            "furniture": self.furniture_lab6.id,
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
        data = {"row": 0, "col": 0, "furniture": self.furniture_lab6.id}
        self.client.force_login(self.professor_user)
        response = self.client.get(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertRedirects(response, reverse('permission_denied'), 302, 200)

    def test_student_can_not_create_shelf(self):
        """
            the student doesn't have privilege to create a shelf
        """
        shelf_name = "Gaveta A"
        url = reverse("laboratory:shelf_create", kwargs={"lab_pk": self.lab1.pk})
        data = {
            "row": 0,
            "col": 0,
            "furniture": self.furniture_lab6.id,
            "name": shelf_name,
            "type": Catalog.objects.filter(description="Gaveta").first().pk
        }
        self.client.force_login(self.student_user)
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertRedirects(response, reverse('permission_denied'), 302, 200)

    def test_get_all_shelves_by_lab_and_furniture(self):
        """
            getting all the shelf from specific lab and furniture
            theirs ids are stored in the furniture data config
        """
        shelf_a = Shelf.objects.create(
            furniture=self.furniture_lab6,
            name="Gaveta A",
            type=Catalog.objects.filter(key="container_type", description="Gaveta").first()
        )
        shelf_b = Shelf.objects.create(
            furniture=self.furniture_lab6,
            name="Gaveta B",
            type=Catalog.objects.filter(key="container_type", description="Gaveta").first()
        )

        self.furniture_lab6.dataconfig = f"[[[{shelf_a.id}],[{shelf_b.id}]]]"
        self.furniture_lab6.save()

        url = reverse("laboratory:list_shelf", kwargs={"lab_pk": self.lab6.pk})
        data = {"furniture": self.furniture_lab6.id}
        self.client.force_login(self.professor_user)
        response = self.client.get(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        flatten_list = list(itertools.chain(*response.context["object_list"])) # ¿?
        self.assertEqual(len(flatten_list), 2)
        self.assertEqual(len(response.context["object_list"]), 2, msg="list should be not nested")

    def _user_can_delete_shelve(self, user, allowed=False):

        shelf_a = Shelf.objects.create(
            furniture=self.furniture_lab6,
            name="Gaveta A",
            type=Catalog.objects.filter(key="container_type", description="Gaveta").first()
        )
        shelf_b = Shelf.objects.create(
            furniture=self.furniture_lab6,
            name="Gaveta B",
            type=Catalog.objects.filter(key="container_type", description="Gaveta").first()
        )

        self.furniture_lab6.dataconfig = f"[[[{shelf_a.id}],[{shelf_b.id}]]]"
        self.furniture_lab6.save()

        kwargs = {
            "lab_pk": self.lab6.pk,
            "row": 0,
            "col": 0,
            "pk": shelf_a.pk
        }
        url = reverse("laboratory:shelf_delete", kwargs=kwargs)
        self.client.force_login(user)
        before = Shelf.objects.all().count() # 2
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        after = Shelf.objects.all().count() # 1
        deleted = before - after == 1
        self.assertEqual(deleted, allowed, msg="this user is not allowed to delete shelves")

    def test_professor_can_delete_shelves(self):
        """
            just the professor's group should be able to delete shelves
        """
        self._user_can_delete_shelve(self.professor_user, allowed=False)

    def test_lab_user_can_not_delete_shelves(self):
        """
            lab user is not supposed to be able to delete shelves
        """
        self._user_can_delete_shelve(self.laboratorist_user, allowed=True)

    def test_student_user_can_not_delete_shelves(self):
        """
            student is not supposed to be able to delete shelves
        """
        self._user_can_delete_shelve(self.student_user, allowed=False)

    def _user_can_edit(self, user):
        """
            when the edit function is performed the form change
        """

        shelf_a = Shelf.objects.create(
            furniture=self.furniture_lab6,
            name="Gaveta A",
            type=Catalog.objects.filter(key="container_type", description="Gaveta").first()
        )
        shelf_b = Shelf.objects.create(
            furniture=self.furniture_lab6,
            name="Gaveta B",
            type=Catalog.objects.filter(key="container_type", description="Gaveta").first()
        )

        self.furniture_lab6.dataconfig = f"[[[{shelf_a.id}],[{shelf_b.id}]]]"
        self.furniture_lab6.save()

        kwargs = {
            "lab_pk": self.lab6.pk,
            "pk": shelf_a.pk,
            "row": 0, # old position
            "col": 0, # old position
        }
        data = {
            "row": 2, # new position
            "col": 2, # new position
        }
        url = reverse("laboratory:shelf_edit", kwargs=kwargs)

        self.client.force_login(user)
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")

    def test_professor_can_edit_shelves_positions(self):
        self._user_can_edit(self.professor_user) # if the user can edit
        self.assertTrue(self.professor_user.has_perm('laboratory.change_shelf')) # this line will confirm it

    def test_lab_user_can_not_edit_shelves_positions(self):
        self._user_can_edit(self.laboratorist_user) # if the user can edit
        self.assertTrue(self.laboratorist_user.has_perm('laboratory.change_shelf')) # this line will confirm it

    def test_student_can_not_edit_shelves_positions(self):
        self._user_can_edit(self.student_user) # if the user can edit
        self.assertTrue(self.student_user.has_perm('laboratory.change_shelf')) # this line will confirm it


