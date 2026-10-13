"""
Segunda pasada de cobertura sobre ``laboratory/api/shelfobject.py``,
``laboratory/shelfobject/serializers.py`` y ``laboratory/shelfobject/utils.py``.

Incluye las pruebas de dos defectos de cajas corregidos aquí:

* aprobar la transferencia de todas las cajas de un objeto cuyo estante de
  origen tiene unidad daba 500 (``move_shelfobject_to`` leía
  ``Object.measurement_unit``, que no existe);
* ``TransferInShelfObjectSerializer`` con cajas y un estante sin capacidad daba
  500 (leía ``TranferObject.amount_to_transfer`` y la clave ``quantity``, que
  ya se había agrupado en ``transfer_object``).
"""

from django.urls import reverse

from laboratory.models import (
    Catalog,
    Furniture,
    Laboratory,
    Shelf,
    ShelfObject,
    TranferObject,
    REQUESTED,
    ACCEPTED,
)
from laboratory.shelfobject import serializers as so_serializers
from laboratory.shelfobject.utils import get_available_objs_by_shelfobject
from laboratory.tests.test_cov_api_base import CovApiBase, UNIDADES, ESTADO_EXCELENTE


class TransferenciaDeCajasTest(CovApiBase):
    def setUp(self):
        super().setUp()
        self.lab2 = Laboratory.objects.get(pk=2)
        self.caja = self.crear_caja(cajas=2)
        mueble = Furniture.objects.create(labroom_id=3, name="Mueble destino", type_id=75)
        self.destino = Shelf.objects.create(
            furniture=mueble, name="Destino", type_id=74, infinity_quantity=True
        )

    def transferencia(self, cajas):
        return TranferObject.objects.create(
            object=self.caja,
            quantity=cajas,
            laboratory_send=self.lab,
            laboratory_received=self.lab2,
            status=REQUESTED,
            is_box=True,
            quantity_units=[
                {"code": "t-%d" % i, "units": 10, "quantity": 20} for i in range(cajas)
            ],
            created_by=self.user,
        )

    def test_aprobar_todas_las_cajas_desde_estante_con_unidad(self):
        Shelf.objects.filter(pk=self.caja.shelf_id).update(measurement_unit_id=UNIDADES)
        transfer = self.transferencia(2)
        response = self.client.post(
            self.url("api-shelfobject-transfer-in-approve", lab=self.lab2),
            data={"transfer_object": transfer.pk, "shelf": self.destino.pk},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.caja.refresh_from_db()
        self.assertEqual(self.caja.shelf, self.destino)
        self.assertEqual(self.caja.in_where_laboratory, self.lab2)
        # Las cajas siguen siendo cajas (antes se iban a convertir en números).
        self.assertEqual([caja["units"] for caja in self.caja.quantity_units], [10, 10])
        transfer.refresh_from_db()
        self.assertEqual(transfer.status, ACCEPTED)

    def test_estante_sin_capacidad_y_menos_cajas_en_el_origen(self):
        self.destino.infinity_quantity = False
        self.destino.quantity = 1
        self.destino.save()
        transfer = self.transferencia(3)  # el origen solo tiene 2 cajas
        serializer = so_serializers.TransferInShelfObjectSerializer(
            data={"transfer_object": transfer.pk, "shelf": self.destino.pk},
            context={"laboratory_id": self.lab2.pk, "organization_id": self.org.pk, "validate_for_approval": True},
        )
        self.assertFalse(serializer.is_valid())
        mensajes = [str(error) for error in serializer.errors["transfer_object"]]
        self.assertTrue(any("boxes available" in mensaje for mensaje in mensajes), mensajes)


class TransferenciaConUnidadSinConversionTest(CovApiBase):
    """Misma unidad en objeto y estante, pero sin ``BaseUnitValues``: la unidad
    coincide (no hay error de unidad) y aun así no hay conversión posible."""

    def test_se_rechaza_con_error_de_estante(self):
        unidad = Catalog.objects.create(key="units", description="Unidad sin base cov2")
        reactivo = ShelfObject.objects.get(pk=2)
        ShelfObject.objects.filter(pk=reactivo.pk).update(measurement_unit=unidad)
        mueble = Furniture.objects.create(labroom_id=3, name="Destino", type_id=75)
        destino = Shelf.objects.create(
            furniture=mueble, name="Destino", type_id=74, infinity_quantity=True, measurement_unit=unidad
        )
        transfer = TranferObject.objects.create(
            object=reactivo, quantity=1, laboratory_send=self.lab,
            laboratory_received=Laboratory.objects.get(pk=2), status=REQUESTED, created_by=self.user,
        )
        serializer = so_serializers.TransferInShelfObjectApproveWithContainerSerializer(
            data={
                "transfer_object": transfer.pk, "shelf": destino.pk, "container_select_option": "clone",
                "container_for_cloning": 4, "available_container": None,
            },
            context={"laboratory_id": 2, "organization_id": self.org.pk, "validate_for_approval": True},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("shelf", serializer.errors)


class EstantesDisponiblesTest(CovApiBase):
    """``get_available_objs_by_shelfobject`` con estantes sin unidad y con
    unidades que no se pueden convertir."""

    def setUp(self):
        super().setUp()
        mueble = Furniture.objects.create(labroom_id=1, name="Mueble cov2", type_id=75)
        self.sin_unidad = Shelf.objects.create(
            furniture=mueble, name="Sin unidad", type_id=74, quantity=100, infinity_quantity=False
        )
        self.otra_unidad = Shelf.objects.create(
            furniture=mueble, name="Unidad sin base", type_id=74, quantity=100, infinity_quantity=False,
            measurement_unit=Catalog.objects.create(key="units", description="Sin base cov2"),
        )
        ShelfObject.objects.create(
            shelf=self.sin_unidad, object_id=6, quantity=3, measurement_unit_id=UNIDADES,
            in_where_laboratory=self.lab, status_id=ESTADO_EXCELENTE, created_by=self.user,
        )
        self.objeto = ShelfObject.objects.get(pk=1)
        self.mueble = mueble

    def test_suma_todo_en_estante_sin_unidad_y_salta_lo_no_convertible(self):
        disponibles = get_available_objs_by_shelfobject(
            Furniture.objects.all(), self.objeto, "shelf", {"pk": self.mueble.pk}
        )
        # El mueble aparece una vez por cada estante candidato que lo admite:
        # solo el estante sin unidad (3 ocupados de 100); el de unidad sin base
        # no tiene conversión y se descarta.
        self.assertEqual(disponibles, [self.mueble.pk])


class ListadoDeMantenimientosSinObjetoTest(CovApiBase):
    def test_sin_objeto_en_la_url_no_lista_nada(self):
        response = self.client.get(
            reverse(
                "laboratory:api-shelfobject-maintenance-list",
                kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "shelfobject": 0},
            ),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["data"], [])
