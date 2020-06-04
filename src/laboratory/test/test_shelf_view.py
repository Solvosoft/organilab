from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode

from laboratory.models import Furniture, Catalog, LaboratoryRoom
from laboratory.test.utils import OrganizationalStructureDataMixin as OrganizationalStructureData



class ShelfViewTestCases(TestCase):

    def setUp(self):
        infrastructure = OrganizationalStructureData()
        infrastructure.setUp()

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
        self.technician_user = infrastructure.uschi1
        self.root_user = infrastructure.uroot


    def test_laboratorist_group_restricted(self):
        """
            laboratoris's group are restricted
        """

        url = reverse("laboratory:shelf_create", kwargs={"lab_pk": self.lab6.pk})
        data = urlencode({"row": 0, "col": 0, "furniture": self.furniture.id})

        self.client.force_login(self.laboratorist_user)
        response = self.client.get(f"{url}?{data}", follow=True)
        self.assertRedirects(response, reverse('permission_denied'), 302, 200)
