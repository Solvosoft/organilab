import json

from django.urls import reverse

from laboratory.models import (
    ShelfObject,
    Shelf,
    Catalog,
    TranferObject,
    ShelfObjectObservation,
    Laboratory,
)
from laboratory.models import REQUESTED, ACCEPTED
from laboratory.tests.test_cov_api_base import (
    CovApiBase,
    UNIDADES,
    MILILITROS,
    LITROS,
    METROS,
    ESTADO_EXCELENTE,
)
from reservations_management.models import ReservedProducts, BORROWED, RETURNED


class CrearCajaApiTest(CovApiBase):
    """Acción ``create_box_shelfobject``: alta de objetos tipo caja."""

    def setUp(self):
        super().setUp()
        self.shelf = Shelf.objects.get(pk=2)
        self.shelf.infinity_quantity = True
        self.shelf.save()
        self.data = {
            "shelf": self.shelf.pk,
            "object": 6,
            "status": ESTADO_EXCELENTE,
            "quantity": 2,
            "measurement_unit": UNIDADES,
            "units_per_box": 10,
            "quantity_box": 3,
            "description": "Cajas de guantes",
        }

    def test_crea_cajas_con_codigos_unicos(self):
        response = self.client.post(
            self.url("api-shelfobject-create-box-shelfobject"),
            data=self.data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        caja = ShelfObject.objects.filter(is_box=True, shelf=self.shelf).latest("pk")
        self.assertEqual(caja.units_per_box, 10)
        self.assertEqual(len(caja.quantity_units), 3)
        codigos = [b["code"] for b in caja.quantity_units]
        self.assertEqual(len(set(codigos)), 3)
        self.assertTrue(all(c.startswith("b%d-" % caja.pk) for c in codigos))
        self.assertTrue(all(b["quantity"] == 20 for b in caja.quantity_units))
        self.assertTrue(
            ShelfObjectObservation.objects.filter(
                shelf_object=caja, description="Cajas de guantes"
            ).exists()
        )

    def test_crea_caja_convirtiendo_a_la_unidad_del_estante(self):
        shelf = Shelf.objects.get(pk=1)  # en mililitros
        shelf.infinity_quantity = True
        shelf.save()
        data = dict(self.data, shelf=shelf.pk, measurement_unit=LITROS, quantity=1, quantity_box=1)
        response = self.client.post(
            self.url("api-shelfobject-create-box-shelfobject"),
            data=data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        caja = ShelfObject.objects.filter(is_box=True, shelf=shelf).latest("pk")
        # 1 litro por unidad = 1000 ml, por 10 unidades de la caja
        self.assertEqual(caja.quantity_units[0]["quantity"], 10000)

    def test_unidad_no_convertible_no_crea_la_caja(self):
        shelf = Shelf.objects.get(pk=1)  # en mililitros
        shelf.infinity_quantity = True
        shelf.save()
        antes = ShelfObject.objects.count()
        data = dict(self.data, shelf=shelf.pk, measurement_unit=METROS)
        response = self.client.post(
            self.url("api-shelfobject-create-box-shelfobject"),
            data=data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("measurement_unit", response.json()["errors"])
        self.assertEqual(ShelfObject.objects.count(), antes)

    def test_datos_invalidos_devuelven_errores(self):
        data = dict(self.data, units_per_box=0)
        response = self.client.post(
            self.url("api-shelfobject-create-box-shelfobject"),
            data=data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("units_per_box", response.json()["errors"])

    def test_cantidad_que_excede_el_estante_se_rechaza(self):
        self.shelf.infinity_quantity = False
        self.shelf.quantity = 1
        self.shelf.save()
        response = self.client.post(
            self.url("api-shelfobject-create-box-shelfobject"),
            data=self.data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("quantity", response.json()["errors"])


class EditarCajaApiTest(CovApiBase):
    """Acciones ``get_box_edit_data`` y ``update_box_shelfobject``."""

    def setUp(self):
        super().setUp()
        self.caja = self.crear_caja()

    def test_datos_de_edicion_de_la_caja(self):
        self.caja.reactive_expiration_date = "2030-01-31"
        self.caja.type_budget = Catalog.objects.create(key="type_budget", description="Fondos")
        self.caja.save()
        response = self.client.get(
            self.url("api-shelfobject-get-box-edit-data", pk=self.caja.pk)
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["object"]["id"], 6)
        self.assertEqual(data["status"]["id"], ESTADO_EXCELENTE)
        self.assertEqual(data["measurement_unit"]["id"], UNIDADES)
        self.assertEqual(data["type_budget"]["text"], "Fondos")
        self.assertEqual(data["reactive_expiration_date"], "31/01/2030")
        self.assertEqual(data["quantity_box"], 3)
        self.assertEqual(data["units_per_box"], 10)

    def test_datos_de_edicion_sin_relaciones_opcionales(self):
        ShelfObject.objects.filter(pk=self.caja.pk).update(
            status=None, quantity_units=[], reactive_expiration_date=None
        )
        response = self.client.get(
            self.url("api-shelfobject-get-box-edit-data", pk=self.caja.pk)
        )
        data = response.json()
        self.assertIsNone(data["status"])
        self.assertIsNone(data["type_budget"])
        self.assertEqual(data["quantity_box"], 0)
        self.assertEqual(data["reactive_expiration_date"], "")

    def test_caja_de_otro_laboratorio_da_404(self):
        otra = self.crear_caja(lab=Laboratory.objects.get(pk=2))
        response = self.client.get(
            self.url("api-shelfobject-get-box-edit-data", pk=otra.pk)
        )
        self.assertEqual(response.status_code, 404)

    def test_actualiza_la_caja_y_deja_observacion(self):
        response = self.client.put(
            self.url("api-shelfobject-update-box-shelfobject", pk=self.caja.pk),
            data={"description": "Revisada", "batch": "L-77"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.caja.refresh_from_db()
        self.assertEqual(self.caja.description, "Revisada")
        self.assertEqual(self.caja.batch, "L-77")
        self.assertTrue(
            ShelfObjectObservation.objects.filter(
                shelf_object=self.caja, description="Revisada"
            ).exists()
        )

    def test_actualizacion_invalida_devuelve_errores(self):
        response = self.client.put(
            self.url("api-shelfobject-update-box-shelfobject", pk=self.caja.pk),
            data={"concentration": "mucho"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("concentration", response.json()["errors"])


class ReservarCajaApiTest(CovApiBase):
    """Acción ``reserve`` con objetos tipo caja y sus validaciones de fechas."""

    def setUp(self):
        super().setUp()
        self.caja = self.crear_caja(units_list=[10, 10, 4])
        inicio, fin = self.fechas_futuras()
        self.data = {
            "shelf_object": self.caja.pk,
            "amount_required": 1.5,
            "initial_date": inicio,
            "final_date": fin,
        }

    def reservar(self, **cambios):
        return self.client.post(
            self.url("api-shelfobject-reserve"), data=dict(self.data, **cambios)
        )

    def test_reserva_cajas_completas_y_parcial(self):
        response = self.reservar()
        self.assertEqual(response.status_code, 200)
        reserva = ReservedProducts.objects.get(shelf_object=self.caja)
        self.assertEqual(
            [(b["code"], b["units"]) for b in reserva.reserved_boxes],
            [("b-0", 10), ("b-1", 5)],
        )

    def test_reserva_parcial_toma_caja_incompleta(self):
        self.caja.quantity_units = [{"code": "b-0", "units": 10, "quantity": 20}, {"code": "b-1", "units": 4, "quantity": 8}]
        self.caja.save()
        response = self.reservar(amount_required=1.3)
        self.assertEqual(response.status_code, 200)
        reserva = ReservedProducts.objects.get(shelf_object=self.caja)
        self.assertEqual(reserva.reserved_boxes[1], {"code": "b-1", "units": 3, "quantity": 8})

    def test_no_hay_suficientes_cajas_completas(self):
        response = self.reservar(amount_required=3)
        self.assertEqual(response.status_code, 400)
        self.assertIn("amount_required", response.json()["errors"])

    def test_ninguna_caja_alcanza_para_la_parte_fraccionaria(self):
        self.caja.quantity_units = [{"code": "b-0", "units": 2, "quantity": 4}]
        self.caja.save()
        response = self.reservar(amount_required=0.5)
        self.assertEqual(response.status_code, 400)
        self.assertIn("amount_required", response.json()["errors"])
        self.assertFalse(ReservedProducts.objects.filter(shelf_object=self.caja).exists())

    def test_fecha_final_antes_de_la_inicial(self):
        response = self.reservar(final_date=self.data["initial_date"], initial_date=self.data["final_date"])
        self.assertEqual(response.status_code, 400)
        self.assertIn("final_date", response.json()["errors"])

    def test_fecha_inicial_en_el_pasado(self):
        inicio, _fin = self.fechas_futuras(dias_inicio=-5)
        response = self.reservar(initial_date=inicio)
        self.assertEqual(response.status_code, 400)
        self.assertIn("initial_date", response.json()["errors"])

    def test_objeto_de_otro_laboratorio(self):
        otra = self.crear_caja(lab=Laboratory.objects.get(pk=2))
        response = self.reservar(shelf_object=otra.pk)
        self.assertEqual(response.status_code, 400)
        self.assertIn("shelf_object", response.json()["errors"])


class DevolverCajaApiTest(CovApiBase):
    """Acción ``return_shelfobject``: devolución de cajas prestadas."""

    def setUp(self):
        super().setUp()
        self.caja = self.crear_caja(units_list=[10, 5])
        inicio, fin = self.fechas_futuras()
        self.reserva = ReservedProducts.objects.create(
            shelf_object=self.caja,
            amount_required=1.5,
            initial_date="2030-01-01T10:00Z",
            final_date="2030-01-02T10:00Z",
            status=BORROWED,
            laboratory=self.lab,
            organization=self.org,
            user=self.user,
            reserved_boxes=[
                {"code": "b-0", "units": 10, "quantity": 20},
                {"code": "b-1", "units": 5, "quantity": 20},
            ],
        )

    def devolver(self, **data):
        data.setdefault("reserved_product", self.reserva.pk)
        return self.client.post(
            self.url("api-shelfobject-return-shelfobject"),
            data=data,
            content_type="application/json",
        )

    def test_devuelve_las_unidades_a_cada_caja(self):
        response = self.devolver()
        self.assertEqual(response.status_code, 200)
        self.caja.refresh_from_db()
        unidades = {b["code"]: b["units"] for b in self.caja.quantity_units}
        self.assertEqual(unidades, {"b-0": 20, "b-1": 10})
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.status, RETURNED)
        observacion = ShelfObjectObservation.objects.filter(shelf_object=self.caja).latest("pk")
        self.assertIn("b-0, b-1", str(observacion.description))

    def test_descripcion_propia_se_conserva(self):
        response = self.devolver(description="Devueltas tras práctica")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ShelfObjectObservation.objects.filter(
                shelf_object=self.caja, description="Devueltas tras práctica"
            ).exists()
        )

    def test_solo_se_devuelven_reservas_prestadas(self):
        ReservedProducts.objects.filter(pk=self.reserva.pk).update(status=0)
        response = self.devolver()
        self.assertEqual(response.status_code, 400)
        self.assertIn("reserved_product", response.json()["errors"])

    def test_reserva_que_no_es_de_caja(self):
        response = self.devolver(reserved_product=1)
        self.assertEqual(response.status_code, 400)
        self.assertIn("reserved_product", response.json()["errors"])

    def test_reserva_de_otro_laboratorio(self):
        ShelfObject.objects.filter(pk=self.caja.pk).update(in_where_laboratory_id=2)
        response = self.devolver()
        self.assertEqual(response.status_code, 400)
        self.assertIn("reserved_product", response.json()["errors"])
        self.caja.refresh_from_db()
        self.assertEqual(self.caja.quantity_units[0]["units"], 10)


class TransferirCajaApiTest(CovApiBase):
    """Transferencia de cajas: ``transfer_out`` y ``transfer_in_approve``."""

    def setUp(self):
        super().setUp()
        self.lab2 = Laboratory.objects.get(pk=2)
        self.caja = self.crear_caja(units_list=[4, 10, 7])

    def test_transfer_out_toma_las_cajas_mas_llenas(self):
        response = self.client.post(
            self.url("api-shelfobject-transfer-out"),
            data={"shelf_object": self.caja.pk, "amount_to_transfer": 2, "laboratory": self.lab2.pk},
        )
        self.assertEqual(response.status_code, 200)
        transfer = TranferObject.objects.get(object=self.caja)
        self.assertTrue(transfer.is_box)
        self.assertEqual([b["units"] for b in transfer.quantity_units], [10, 7])

    def test_transfer_out_con_mas_cajas_de_las_disponibles(self):
        response = self.client.post(
            self.url("api-shelfobject-transfer-out"),
            data={"shelf_object": self.caja.pk, "amount_to_transfer": 5, "laboratory": self.lab2.pk},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("amount_to_transfer", response.json()["errors"])

    def test_transfer_out_de_objeto_de_otro_laboratorio(self):
        otra = self.crear_caja(lab=self.lab2)
        response = self.client.post(
            self.url("api-shelfobject-transfer-out"),
            data={"shelf_object": otra.pk, "amount_to_transfer": 1, "laboratory": 1},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("shelf_object", response.json()["errors"])
        self.assertFalse(TranferObject.objects.filter(object=otra).exists())

    def test_transfer_out_a_laboratorio_de_otra_organizacion(self):
        from laboratory.models import OrganizationStructure

        org_ajena = OrganizationStructure.objects.create(name="Org sin relación")
        lab_ajeno = Laboratory.objects.create(name="Lab ajeno", organization=org_ajena)
        response = self.client.post(
            self.url("api-shelfobject-transfer-out"),
            data={"shelf_object": self.caja.pk, "amount_to_transfer": 1, "laboratory": lab_ajeno.pk},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(TranferObject.objects.filter(object=self.caja).exists())

    def test_transfer_out_mayor_a_la_cantidad_disponible(self):
        response = self.client.post(
            self.url("api-shelfobject-transfer-out"),
            data={"shelf_object": 6, "amount_to_transfer": 50, "laboratory": self.lab2.pk},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("amount_to_transfer", response.json()["errors"])

    def transferencia(self, cajas):
        return TranferObject.objects.create(
            object=self.caja,
            quantity=len(cajas),
            laboratory_send=self.lab,
            laboratory_received=self.lab2,
            status=REQUESTED,
            is_box=True,
            quantity_units=cajas,
            created_by=self.user,
        )

    def aprobar(self, transfer, shelf):
        return self.client.post(
            self.url("api-shelfobject-transfer-in-approve", lab=self.lab2),
            data={"transfer_object": transfer.pk, "shelf": shelf.pk},
            content_type="application/json",
        )

    def estante_lab2(self, unit=None):
        return Shelf.objects.create(
            furniture=self.furniture_lab2(),
            name="Destino",
            type_id=74,
            measurement_unit_id=unit,
            infinity_quantity=True,
        )

    def furniture_lab2(self):
        from laboratory.models import Furniture

        return Furniture.objects.create(labroom_id=3, name="Mueble destino", type_id=75)

    def test_aprobar_todas_las_cajas_mueve_el_objeto(self):
        transfer = self.transferencia(list(self.caja.quantity_units))
        destino = self.estante_lab2()
        response = self.aprobar(transfer, destino)
        self.assertEqual(response.status_code, 200, response.content)
        self.caja.refresh_from_db()
        self.assertEqual(self.caja.in_where_laboratory, self.lab2)
        self.assertEqual(self.caja.shelf, destino)
        transfer.refresh_from_db()
        self.assertEqual(transfer.status, ACCEPTED)

    def test_aprobar_todas_las_cajas_en_mililitros(self):
        ShelfObject.objects.filter(pk=self.caja.pk).update(measurement_unit_id=MILILITROS)
        transfer = self.transferencia(list(self.caja.quantity_units))
        destino = self.estante_lab2(unit=LITROS)
        response = self.aprobar(transfer, destino)
        self.assertEqual(response.status_code, 200, response.content)
        self.caja.refresh_from_db()
        self.assertEqual(self.caja.measurement_unit_id, LITROS)

    def test_aprobar_parte_de_las_cajas_divide_el_objeto(self):
        transfer = self.transferencia([{"code": "b-1", "units": 10, "quantity": 20}])
        destino = self.estante_lab2()
        response = self.aprobar(transfer, destino)
        self.assertEqual(response.status_code, 200, response.content)
        nueva = ShelfObject.objects.get(shelf=destino)
        self.assertTrue(nueva.is_box)
        self.assertEqual(nueva.in_where_laboratory, self.lab2)
        self.caja.refresh_from_db()
        self.assertEqual(len(self.caja.quantity_units), 2)

    def test_denegar_transferencia_de_otro_laboratorio(self):
        transfer = self.transferencia(list(self.caja.quantity_units))
        response = self.client.delete(
            self.url("api-shelfobject-transfer-in-deny"),
            data={"transfer_object": transfer.pk},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("transfer_object", response.json()["errors"])
        self.assertTrue(TranferObject.objects.filter(pk=transfer.pk).exists())

    def test_aprobar_parte_de_un_material_en_mililitros(self):
        material = ShelfObject.objects.get(pk=11)  # 2 ml del objeto 4
        transfer = TranferObject.objects.create(
            object=material, quantity=1, laboratory_send=self.lab, laboratory_received=self.lab2,
            status=REQUESTED, created_by=self.user,
        )
        destino = self.estante_lab2(unit=MILILITROS)
        response = self.aprobar(transfer, destino)
        self.assertEqual(response.status_code, 200, response.content)
        material.refresh_from_db()
        self.assertEqual(material.quantity, 1)
        nuevo = ShelfObject.objects.get(shelf=destino)
        self.assertEqual(nuevo.quantity, 1)
        self.assertEqual(nuevo.in_where_laboratory, self.lab2)

    def test_aprobar_parte_de_las_cajas_en_mililitros(self):
        ShelfObject.objects.filter(pk=self.caja.pk).update(measurement_unit_id=MILILITROS)
        transfer = self.transferencia([{"code": "b-1", "units": 10, "quantity": 20}])
        destino = self.estante_lab2(unit=MILILITROS)
        response = self.aprobar(transfer, destino)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(ShelfObject.objects.filter(shelf=destino, is_box=True).exists())
