# encoding: utf-8
"""Forma y coste del árbol: que no crezca con el mapa.

El árbol sustituye a una plantilla que consultaba la base de datos por cada
celda, así que lo que hay que demostrar no es un número bonito sino que el
coste **no depende del tamaño del laboratorio**: duplicar los muebles y los
estantes no puede duplicar las consultas.

Dos cuidados que hacen falta para que la medida signifique algo:

* ``TreeBuilder`` **materializa los QR que faltan**, así que la primera llamada
  escribe y la segunda no.  Se calienta antes de medir.
* Django limpia la caché de ``ContentType`` entre pruebas, y esos lookups se
  cuentan.  También se calientan.

Esta clase no usa ``RolPermissionMixin``: los ``ProfilePermission`` que crea
cambian el número de consultas del middleware, que es justo lo que se mide.
"""

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from laboratory import dataconfig
from laboratory.models import (
    Furniture,
    LaboratoryRoom,
    Object,
    Shelf,
    ShelfObject,
)
from laboratory.tests.utils import BaseLaboratorySetUpTest
from presentation.models import QRModel


class TreeQueryShapeTest(BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        self.user.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="laboratory",
                codename__in=[
                    "view_laboratoryroom", "view_furniture", "view_shelf",
                    "view_shelfobject",
                ],
            )
        )
        self.user = type(self.user).objects.get(pk=self.user.pk)
        self.client.force_login(self.user)
        self.kwargs = {"org_pk": self.org.pk, "lab_pk": self.lab.pk}
        self.url = reverse("laboratory:api-labview-tree-list", kwargs=self.kwargs)

        for model in (LaboratoryRoom, Furniture, Shelf, QRModel, ShelfObject):
            ContentType.objects.get_for_model(model)
        self.warm()

    def warm(self):
        """Crea los QR que falten para que la medición no los pague."""
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.get(self.url + "?risk=1").status_code, 200)

    def count(self, query=""):
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(self.url + query)
        self.assertEqual(response.status_code, 200)
        return len(captured)

    def grow_the_map(self):
        """Cinco muebles más, con tres estantes y un objeto cada uno."""
        room = LaboratoryRoom.objects.filter(laboratory=self.lab).first()
        model_furniture = Furniture.objects.get(pk=1)
        model_shelf = Shelf.objects.get(pk=1)
        reactive = Object.objects.filter(type=Object.REACTIVE).first()

        for index in range(5):
            furniture = Furniture.objects.create(
                labroom=room, name="Mueble %d" % index,
                type=model_furniture.type, dataconfig="[[[]]]",
            )
            matrix = [[[]], [[], []]]
            for position in range(3):
                shelf = Shelf.objects.create(
                    furniture=furniture, name="Estante %d-%d" % (index, position),
                    type=model_shelf.type, quantity=10,
                    measurement_unit=model_shelf.measurement_unit,
                )
                matrix[position % 2][position % 2] = [shelf.pk]
                ShelfObject.objects.create(
                    object=reactive, shelf=shelf, quantity=1, limit_quantity=0,
                    measurement_unit=model_shelf.measurement_unit,
                    in_where_laboratory=self.lab,
                )
            furniture.dataconfig = dataconfig.dump(matrix)
            furniture.save()
        self.warm()

    # -- pruebas -----------------------------------------------------------

    def test_the_tree_does_not_grow_with_the_map(self):
        before = self.count()
        self.grow_the_map()
        self.assertEqual(self.count(), before)

    def test_the_risk_overlay_costs_the_same_extra_on_a_bigger_map(self):
        extra_before = self.count("?risk=1") - self.count()
        self.grow_the_map()
        self.assertEqual(self.count("?risk=1") - self.count(), extra_before)

    def test_asking_without_risk_does_not_pay_for_it(self):
        self.assertLess(self.count(), self.count("?risk=1"))

    def test_a_missing_qr_is_created_once_and_never_again(self):
        QRModel.objects.all().delete()

        with CaptureQueriesContext(connection) as first:
            self.client.get(self.url)
        created = [
            query for query in first.captured_queries
            if "INSERT" in query["sql"].upper() and "qrmodel" in query["sql"].lower()
        ]
        self.assertTrue(created, "el árbol debería materializar los QR que faltan")

        with CaptureQueriesContext(connection) as second:
            self.client.get(self.url)
        self.assertEqual(
            [
                query for query in second.captured_queries
                if "INSERT" in query["sql"].upper()
                and "qrmodel" in query["sql"].lower()
            ],
            [],
        )

    def test_the_table_does_not_grow_with_the_shelf(self):
        table = reverse(
            "laboratory:api-labview-shelfobjecttable-list", kwargs=self.kwargs
        )
        shelf = Shelf.objects.get(pk=1)

        def count_table():
            with CaptureQueriesContext(connection) as captured:
                response = self.client.get(table + "?shelf=%d" % shelf.pk)
            self.assertEqual(response.status_code, 200)
            return len(captured)

        before = count_table()
        reactive = Object.objects.filter(type=Object.REACTIVE).first()
        for _index in range(20):
            ShelfObject.objects.create(
                object=reactive, shelf=shelf, quantity=1, limit_quantity=0,
                measurement_unit=shelf.measurement_unit,
                in_where_laboratory=self.lab,
            )
        # El diccionario de acciones se calcula por fila: es el candidato
        # natural a un N+1 que nadie ve hasta que el estante está lleno.
        self.assertEqual(count_table(), before)
