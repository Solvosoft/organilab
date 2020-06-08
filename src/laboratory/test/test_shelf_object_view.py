from django.test import TestCase
from django.urls import reverse

from laboratory.models import LaboratoryRoom, Furniture, Catalog, Shelf, ShelfObject, Object
from laboratory.test.utils import OrganizationalStructureDataMixin as OrganizationalStructureData


class ShelfObjectViewTestCases(TestCase):
    """
        Tests for shelfobject view
    """

    def setUp(self):
        self.infrastructure = OrganizationalStructureData()
        self.infrastructure.setUp()

        self.student_user = self.infrastructure.usch4
        self.laboratorist_user = self.infrastructure.usch6_i1
        self.professor_user = self.infrastructure.uschi1
        self.root_user = self.infrastructure.uroot

        self.room_lab6 = LaboratoryRoom.objects.create(name="Laboratorio alfa")

        self.infrastructure.lab6.rooms.add(self.room_lab6)
        self.infrastructure.lab6.save()

        self.furniture_lab6 = Furniture.objects.create(
            labroom=self.room_lab6,
            name="Mueble X",
            type=Catalog.objects.filter(key="furniture_type", description="Estante").first()
        )

        self.shelf = Shelf.objects.create(
            furniture=self.furniture_lab6,
            name="Gaveta B",
            type=Catalog.objects.filter(key="container_type", description="Gaveta").first()
        )

        self.object = Object.objects.create(
            code ="CEL333",
            name= "celdas espectronic 20",
            type=1,
            description="Equipo que permite realizar medidas de proporciones de longitud de onda absorbida, en un rango de trabajo comprendido entre 340 y 950 nm, con una precisi\u00f3n de 2,5 nm en longitud de onda y de 20 nm en banda espectral. Dispone de conexión a PC por puerto RS232.",
        )

        self.unit = Catalog.objects.create(
            key="units",
            description="Unidades"
        )

    def test_lab_group_can_get_shelf_object_form(self):
        """
            laboratory's group must be the only ones
            who can access this creation form
        """
        url = reverse("laboratory:shelfobject_create", kwargs={"lab_pk": self.infrastructure.lab6.pk})
        self.client.force_login(self.laboratorist_user)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")

    def test_professor_can_not_get_shelf_object_form(self):
        """
            Professor's does not have laboratory.add_shelfobject
            permission they must be redirected
        """
        url = reverse("laboratory:shelfobject_create", kwargs={"lab_pk": self.infrastructure.lab6.pk})
        self.client.force_login(self.professor_user)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertRedirects(response, reverse('permission_denied'), 302, 200)

    def test_student_can_not_get_shelf_object_form(self):
        """
            Student's does not have laboratory.add_shelfobject
            permission they must be redirected
        """
        url = reverse("laboratory:shelfobject_create", kwargs={"lab_pk": self.infrastructure.lab6.pk})
        self.client.force_login(self.student_user)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertRedirects(response, reverse('permission_denied'), 302, 200)

    def test_lab_group_can_create_shelf_object(self):
        """
            in order to create a shelfobject the laboratory.add_shelfobject permission
            is required, just the lab's group must be able to create
        """
        data = {
            "row": 0,
            "col": 0,
            "shelf": self.shelf.id,
            "quantity": 100,
            "limit_quantity": 10,
            "object": self.object.id,
            "measurement_unit": self.unit.id
        }
        url = reverse("laboratory:shelfobject_create", kwargs={"lab_pk": self.infrastructure.lab6.pk})
        self.client.force_login(self.laboratorist_user)
        self.assertEqual(ShelfObject.objects.all().count(), 0)
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ShelfObject.objects.all().count(), 1)

    def test_professor_group_can_not_create_shelf_object(self):
        """
            Professors's group are not supposed to be able to create a shelf-object
        """
        data = {
            "row": 0,
            "col": 0,
            "shelf": self.shelf.id,
            "quantity": 100,
            "limit_quantity": 10,
            "object": self.object.id,
            "measurement_unit": self.unit.id
        }
        url = reverse("laboratory:shelfobject_create", kwargs={"lab_pk": self.infrastructure.lab6.pk})
        self.client.force_login(self.laboratorist_user)
        self.assertEqual(ShelfObject.objects.all().count(), 0)
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ShelfObject.objects.all().count(), 0)

    def test_student_group_can_not_create_shelf_object(self):
        """
            Students's group are not supposed to be able to create a shelf-object
        """
        data = {
            "row": 0,
            "col": 0,
            "shelf": self.shelf.id,
            "quantity": 100,
            "limit_quantity": 10,
            "object": self.object.id,
            "measurement_unit": self.unit.id
        }
        url = reverse("laboratory:shelfobject_create", kwargs={"lab_pk": self.infrastructure.lab6.pk})
        self.client.force_login(self.laboratorist_user)
        self.assertEqual(ShelfObject.objects.all().count(), 0)
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ShelfObject.objects.all().count(), 0)