# encoding: utf-8
"""Aislamiento entre inquilinos: tener la capacidad no es tenerla en cualquier sitio.

El labview toma el ámbito del **prefijo de la ruta**, nunca del cuerpo, porque
quién puede nombrar qué laboratorio es una decisión de autorización y las
``permission_classes`` de DRF son por modelo, no por objeto.

Aquí se construye un segundo inquilino limpio en vez de reutilizar el del
fixture: ``laboratory_data.json`` relaciona el laboratorio 1 con las cuatro
organizaciones (``OrganizationStructureRelations`` 1 a 4), así que casi
cualquier prefijo pasa el control de organización y la prueba no probaría nada.

Cuidado al leer los 403: hay dos razones distintas para uno, y se parecen.
``AllPermissionByAction`` lo devuelve cuando falta la capacidad;
``PermissionByLaboratoryInOrganization`` cuando el usuario no pertenece a la
organización o la organización no manda sobre el laboratorio.  Por eso los dos
casos se separan **por construcción**, no por el código de estado.
"""

import json

from django.urls import reverse

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.api.labview.tree_builder import TREE_PERMISSIONS
from laboratory.models import (
    Furniture,
    Laboratory,
    LaboratoryRoom,
    OrganizationStructure,
    OrganizationStructureRelations,
    Shelf,
    UserOrganization,
)
from laboratory.tests.labview.utils import RolPermissionMixin
from laboratory.tests.utils import BaseLaboratorySetUpTest


class LabviewTenantIsolationTest(RolPermissionMixin, BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        self.user = self.strip_effective_permissions(self.user)

        # Inquilino B, construido limpio: su organización no manda sobre ningún
        # laboratorio del fixture y su usuario no pertenece a la del inquilino A.
        self.user_b = self.strip_effective_permissions(
            type(self.user).objects.get(username="renatafg")
        )
        self.org_b = OrganizationStructure.objects.create(name="Organización B")
        UserOrganization.objects.get_or_create(
            user=self.user_b, organization=self.org_b, type_in_organization=3
        )
        self.lab_b = Laboratory.objects.create(
            name="Laboratorio B", organization=self.org_b
        )
        OrganizationStructureRelations.objects.create(
            organization=self.org_b, content_object=self.lab_b
        )
        self.room_b = LaboratoryRoom.objects.create(
            name="Sala B", laboratory=self.lab_b, created_by=self.user_b
        )
        model = Furniture.objects.get(pk=1)
        self.furniture_b = Furniture.objects.create(
            labroom=self.room_b, name="Mueble B", type=model.type,
            dataconfig="[[[]]]",
        )
        shelf_model = Shelf.objects.get(pk=1)
        self.shelf_b = Shelf.objects.create(
            furniture=self.furniture_b, name="Estante B", type=shelf_model.type,
            quantity=1, measurement_unit=shelf_model.measurement_unit,
        )

        self.everything = list(TREE_PERMISSIONS)

    def url(self, name, org, lab, **extra):
        return reverse(
            "laboratory:" + name,
            kwargs={"org_pk": org.pk, "lab_pk": lab.pk, **extra},
        )

    # -- el ámbito manda sobre la capacidad --------------------------------

    def test_every_capability_in_one_lab_reaches_nothing_in_the_other(self):
        """El 403 aquí sólo puede venir de la capacidad que falta en ese ámbito.

        Se hace miembro de la organización B a propósito, para que el control
        de pertenencia pase y no tape lo que se quiere medir.
        """
        self.org_b.users.add(self.user)
        self.user = self.set_capabilities(self.user, self.everything, scope=self.lab)

        self.assertTrue(user_is_allowed_on_organization(self.user, self.org_b))
        response = self.client.get(
            self.url("api-labview-tree-list", self.org_b, self.lab_b)
        )
        self.assertEqual(response.status_code, 403)

    def test_the_capability_granted_in_that_lab_lets_the_same_user_in(self):
        """La contraprueba exacta de la anterior: sólo cambia el ámbito."""
        self.org_b.users.add(self.user)
        self.user = self.set_capabilities(self.user, self.everything, scope=self.lab_b)

        response = self.client.get(
            self.url("api-labview-tree-list", self.org_b, self.lab_b)
        )
        self.assertEqual(response.status_code, 200)

    def test_the_same_capability_granted_in_the_other_lab_does_reach_it(self):
        """La contraprueba: lo que cambia es el ámbito, no el rol."""
        self.user_b = self.set_capabilities(
            self.user_b, self.everything, scope=self.lab_b
        )
        response = self.client.get(
            self.url("api-labview-tree-list", self.org_b, self.lab_b)
        )
        self.assertEqual(response.status_code, 200)

    def test_the_tree_never_shows_the_other_tenants_rooms(self):
        self.user = self.set_capabilities(self.user, self.everything, scope=self.lab)
        tree = self.client.get(
            self.url("api-labview-tree-list", self.org, self.lab)
        ).json()

        names = {room["name"] for room in tree["rooms"]}
        self.assertNotIn("Sala B", names)
        furniture = [
            item for room in tree["rooms"] for item in room["furniture"]
        ]
        self.assertNotIn(self.furniture_b.pk, {item["id"] for item in furniture})

    def test_a_pk_of_the_other_tenant_is_not_found_rather_than_forbidden(self):
        """Lo decide ``get_queryset``, no el permiso: la fila no existe aquí."""
        self.user = self.set_capabilities(self.user, self.everything, scope=self.lab)
        for name, method, payload in (
            ("api-labview-shelf-move", "put", {"row": 0, "col": 0}),
            ("api-labview-furniture-add-row", "post", {"index": 0}),
        ):
            with self.subTest(endpoint=name):
                pk = (
                    self.shelf_b.pk if "shelf" in name else self.furniture_b.pk
                )
                response = getattr(self.client, method)(
                    self.url("%s" % name, self.org, self.lab, pk=pk),
                    data=json.dumps(payload),
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 404, response.content)

    def test_a_non_member_of_the_organization_is_refused_even_with_everything(self):
        """El otro 403: la capacidad está, la pertenencia no."""
        self.user_b = self.set_capabilities(
            self.user_b, self.everything, scope=self.lab
        )
        response = self.client.get(
            self.url("api-labview-tree-list", self.org, self.lab)
        )
        self.assertEqual(response.status_code, 403)

    def test_the_page_itself_is_refused_across_tenants(self):
        self.user = self.set_capabilities(self.user, self.everything, scope=self.lab)
        response = self.client.get(
            reverse(
                "laboratory:labview",
                kwargs={"org_pk": self.org_b.pk, "lab_pk": self.lab_b.pk},
            ),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 403)
