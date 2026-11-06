import json
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest import mock

from django.urls import reverse
from django_celery_beat.models import PeriodicTask

from laboratory.models import ShelfObjectObservation
from reservations_management import functions
from reservations_management.api.serializers import ValidateReservedProductsSerializer
from reservations_management.models import (
    ReservedProducts,
    ReservationTasks,
    REQUESTED,
    RETURNED,
)
from reservations_management.tests.base import ReservationsBaseTest


class FechasYSuperposicionTest(ReservationsBaseTest):
    def test_superposicion_de_rangos(self):
        inicio = self.ahora
        self.assertGreater(
            functions.get_dates_overlap(
                inicio, inicio + timedelta(days=5), inicio + timedelta(days=2), inicio + timedelta(days=8)
            ),
            0,
        )
        self.assertEqual(
            functions.get_dates_overlap(
                inicio, inicio + timedelta(days=1), inicio + timedelta(days=10), inicio + timedelta(days=12)
            ),
            0,
        )

    def test_cantidad_reservada_solo_cuenta_las_superpuestas(self):
        objeto = self.crear_objeto_estante()
        solicitado = self.crear_producto(objeto, amount=1)
        superpuesto = self.crear_producto(objeto, amount=5)
        lejano = self.crear_producto(objeto, amount=7, inicio=30, fin=35)
        self.assertEqual(
            functions.verify_reserved_products_overlap(solicitado, [superpuesto, lejano]), 5
        )


class StockDeProductosReservadosTest(ReservationsBaseTest):
    """`verify_reserved_shelf_objects_stock`: tomar lo que falta de otras reservas."""

    def test_otro_objeto_reservado_cubre_el_faltante(self):
        solicitado = self.crear_producto(self.crear_objeto_estante(quantity=5), amount=10)
        otro = self.crear_producto(self.crear_objeto_estante(quantity=100), amount=10)
        faltante, valido, nuevos = functions.verify_reserved_shelf_objects_stock(solicitado, -5, [otro])
        self.assertEqual(faltante, 0)
        self.assertTrue(valido)
        self.assertEqual(len(nuevos), 1)
        self.assertEqual(nuevos[0].amount_required, 5)
        self.assertEqual(nuevos[0].shelf_object, otro.shelf_object)
        # El producto nuevo conserva la organización y el laboratorio del original
        self.assertEqual(nuevos[0].organization, self.org)
        self.assertEqual(nuevos[0].laboratory, self.lab)

    def test_objeto_insuficiente_se_toma_parcial_y_se_salta(self):
        solicitado = self.crear_producto(self.crear_objeto_estante(quantity=5), amount=10)
        escaso = self.crear_objeto_estante(quantity=10)
        reserva = self.crear_producto(escaso, amount=8)
        misma = self.crear_producto(escaso, amount=1)
        faltante, valido, nuevos = functions.verify_reserved_shelf_objects_stock(
            solicitado, -5, [reserva, misma]
        )
        # 10 - (1 reservado + 8 requeridos) = 1 disponible
        self.assertEqual(faltante, -4)
        self.assertFalse(valido)
        self.assertEqual([p.amount_required for p in nuevos], [1])

    def test_objeto_totalmente_reservado_no_aporta(self):
        solicitado = self.crear_producto(self.crear_objeto_estante(quantity=5), amount=10)
        lleno = self.crear_objeto_estante(quantity=10)
        self.crear_producto(lleno, amount=10)
        fuera_de_rango = self.crear_producto(lleno, amount=1, inicio=30, fin=35)
        faltante, valido, nuevos = functions.verify_reserved_shelf_objects_stock(
            solicitado, -5, [fuera_de_rango]
        )
        self.assertEqual((faltante, valido, nuevos), (-5, False, []))

    def test_laboratorio_invalido_no_rompe_el_calculo(self):
        solicitado = self.crear_producto(self.crear_objeto_estante(quantity=5), amount=10)
        otro = self.crear_objeto_estante(quantity=100)
        producto = SimpleNamespace(
            id=0,
            shelf_object=otro,
            laboratory="no-numérico",
            amount_required=10,
            initial_date=solicitado.initial_date,
            final_date=solicitado.final_date,
        )
        faltante, valido, nuevos = functions.verify_reserved_shelf_objects_stock(solicitado, -5, [producto])
        self.assertEqual(faltante, 0)
        self.assertTrue(valido)

    def test_sin_stock_ni_reservas_es_invalido(self):
        solicitado = self.crear_producto(self.crear_objeto_estante(quantity=5), amount=10)
        self.assertEqual(
            functions.verify_reserved_shelf_objects_stock(solicitado, -5, []), (-5, False, [])
        )


class StockDisponibleTest(ReservationsBaseTest):
    """`verify_available_shelf_objects_stock`: tomar lo que falta de objetos libres."""

    def setUp(self):
        super().setUp()
        self.solicitado = self.crear_producto(self.crear_objeto_estante(quantity=5), amount=10)

    def test_un_objeto_libre_cubre_el_faltante(self):
        libre = self.crear_objeto_estante(quantity=10)
        faltante, valido, nuevos = functions.verify_available_shelf_objects_stock(self.solicitado, -5, [libre])
        self.assertEqual((faltante, valido), (0, True))
        self.assertEqual(nuevos[0].amount_required, 5)

    def test_varios_objetos_libres_suman_el_faltante(self):
        poco = self.crear_objeto_estante(quantity=3)
        mucho = self.crear_objeto_estante(quantity=10)
        faltante, valido, nuevos = functions.verify_available_shelf_objects_stock(
            self.solicitado, -5, [poco, mucho]
        )
        # Del segundo objeto solo se toma lo que sigue faltando (2), no los 5 originales
        self.assertEqual((faltante, valido), (0, True))
        self.assertEqual([p.amount_required for p in nuevos], [3, 2])

    def test_objetos_libres_insuficientes(self):
        poco = self.crear_objeto_estante(quantity=3)
        faltante, valido, nuevos = functions.verify_available_shelf_objects_stock(self.solicitado, -5, [poco])
        self.assertEqual((faltante, valido), (-2, False))
        self.assertEqual(len(nuevos), 1)

    def test_sin_objetos_libres_es_invalido(self):
        self.assertEqual(
            functions.verify_available_shelf_objects_stock(self.solicitado, -5, []), (-5, False, [])
        )


class ValidarReservacionTest(ReservationsBaseTest):
    def validar(self, producto, org_pk=1):
        return self.client.get(
            reverse("reservations_management:validate_reservation", kwargs={"org_pk": org_pk}),
            data={"id": producto.pk},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    def test_stock_suficiente_sin_reservas(self):
        solicitado = self.crear_producto(self.crear_objeto_estante(quantity=100), amount=10, status=REQUESTED)
        respuesta = self.validar(solicitado)
        self.assertEqual(respuesta.json(), {"is_valid": True, "available_quantity": 10})

    def test_stock_suficiente_con_otras_reservas(self):
        objeto = self.crear_objeto_estante(quantity=100)
        self.crear_producto(objeto, amount=20)
        solicitado = self.crear_producto(objeto, amount=10, status=REQUESTED)
        respuesta = self.validar(solicitado)
        self.assertEqual(respuesta.json(), {"is_valid": True, "available_quantity": 10})

    def test_faltante_cubierto_por_otra_reserva_crea_producto_y_tarea(self):
        solicitado = self.crear_producto(self.crear_objeto_estante(quantity=5), amount=10, status=REQUESTED)
        otro = self.crear_producto(self.crear_objeto_estante(quantity=100), amount=10)
        respuesta = self.validar(solicitado)
        self.assertEqual(respuesta.json(), {"is_valid": True, "available_quantity": 5})
        nuevo = ReservedProducts.objects.get(shelf_object=otro.shelf_object, amount_required=5)
        self.assertTrue(PeriodicTask.objects.filter(name=f"decrease_stock_{nuevo.pk}").exists())

    def test_faltante_cubierto_por_objeto_libre(self):
        solicitado = self.crear_producto(self.crear_objeto_estante(quantity=5), amount=10, status=REQUESTED)
        libre = self.crear_objeto_estante(quantity=20)
        respuesta = self.validar(solicitado)
        self.assertEqual(respuesta.json(), {"is_valid": True, "available_quantity": 5})
        self.assertTrue(ReservedProducts.objects.filter(shelf_object=libre, amount_required=5).exists())

    def test_faltante_sin_cubrir_no_crea_productos(self):
        solicitado = self.crear_producto(self.crear_objeto_estante(quantity=5), amount=10, status=REQUESTED)
        libre = self.crear_objeto_estante(quantity=2)
        antes = ReservedProducts.objects.count()
        respuesta = self.validar(solicitado)
        self.assertEqual(respuesta.json(), {"is_valid": False, "available_quantity": 5})
        self.assertEqual(ReservedProducts.objects.count(), antes)
        self.assertFalse(ReservedProducts.objects.filter(shelf_object=libre).exists())

    def test_reserva_vencida_no_es_valida(self):
        solicitado = self.crear_producto(self.crear_objeto_estante(), inicio=-5, fin=-1, status=REQUESTED)
        self.assertEqual(self.validar(solicitado).json(), {"is_valid": False, "available_quantity": -1})

    def test_organizacion_ajena_es_rechazada(self):
        solicitado = self.crear_producto(self.crear_objeto_estante(), status=REQUESTED)
        self.assertEqual(self.validar(solicitado, org_pk=self.otra_org.pk).status_code, 403)

    def test_serializer_rechaza_producto_de_otra_organizacion(self):
        solicitado = self.crear_producto(self.crear_objeto_estante(), status=REQUESTED)
        serializer = ValidateReservedProductsSerializer(
            data={"id": solicitado.pk}, context={"organization_id": self.otra_org.pk}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("id", serializer.errors)


class ProductoYCantidadTest(ReservationsBaseTest):
    def test_producto_en_cajas_devuelve_cajas(self):
        caja = self.crear_caja()
        producto = self.crear_producto(caja, amount=1, reserved_boxes=[{"code": "b-1", "units": 4}])
        respuesta = self.client.get(
            reverse("reservations_management:get_product_name_and_quantity", kwargs={"org_pk": 1}),
            data={"id": producto.pk},
        )
        datos = respuesta.json()
        self.assertTrue(datos["product_is_box"])
        self.assertEqual(datos["product_quantity"], 2)
        self.assertEqual(datos["reserved_boxes"], [{"code": "b-1", "units": 4}])


class AumentarStockTest(ReservationsBaseTest):
    def aumentar(self, producto, **params):
        return self.client.get(
            reverse("reservations_management:increase_stock", kwargs={"org_pk": 1}),
            data={"id": producto.pk, **params},
        ).json()

    def producto_en_cajas(self):
        caja = self.crear_caja()
        return self.crear_producto(
            caja, amount=1, reserved_boxes=[{"code": "b-1", "units": 4}, {"code": "b-2", "units": 5}]
        )

    def test_cajas_con_json_invalido(self):
        datos = self.aumentar(self.producto_en_cajas(), boxes_to_return="{no-json")
        self.assertFalse(datos["was_increase"])
        self.assertIn("error", datos)

    def test_cajas_sin_seleccion(self):
        datos = self.aumentar(self.producto_en_cajas(), boxes_to_return="[]")
        self.assertFalse(datos["was_increase"])
        self.assertIn("error", datos)

    def comprobar_devolucion(self, producto):
        datos = self.aumentar(
            producto, boxes_to_return=json.dumps([{"code": "b-1", "units": 4}, {"code": "b-2", "units": 0}])
        )
        self.assertTrue(datos["was_increase"])
        producto.refresh_from_db()
        producto.shelf_object.refresh_from_db()
        unidades = {b["code"]: b for b in producto.shelf_object.quantity_units}
        # b-1 recupera sus 4 unidades; b-2 se devolvió en cero y no se restaura
        self.assertEqual(unidades["b-1"]["units"], 14)
        self.assertEqual(unidades["b-1"]["quantity"], 14)
        self.assertEqual(unidades["b-2"]["units"], 10)
        self.assertEqual(producto.status, RETURNED)
        self.assertEqual(producto.reserved_boxes, [])
        self.assertEqual(producto.amount_returned, 1.0)
        self.assertTrue(
            ShelfObjectObservation.objects.filter(shelf_object=producto.shelf_object).exists()
        )

    def test_devolucion_de_cajas_sin_unidad_en_estante(self):
        self.comprobar_devolucion(self.producto_en_cajas())

    def test_devolucion_de_cajas_con_unidad_en_estante(self):
        self.usar_unidad_en_estante()
        self.comprobar_devolucion(self.producto_en_cajas())

    def test_cantidad_mayor_a_la_reservada_no_se_devuelve(self):
        objeto = self.crear_objeto_estante(quantity=50)
        producto = self.crear_producto(objeto, amount=10)
        self.assertFalse(self.aumentar(producto, amount_to_return=11)["was_increase"])
        objeto.refresh_from_db()
        self.assertEqual(objeto.quantity, 50)


class AsignacionDeCajasTest(ReservationsBaseTest):
    def test_objeto_sin_cajas_no_cambia(self):
        producto = self.crear_producto(self.crear_objeto_estante(), amount=1)
        functions._allocate_boxes_if_needed(producto)
        producto.refresh_from_db()
        self.assertEqual(producto.reserved_boxes, [])

    def test_cajas_ya_asignadas_no_cambian(self):
        producto = self.crear_producto(self.crear_caja(), amount=1, reserved_boxes=[{"code": "b-2", "units": 1}])
        functions._allocate_boxes_if_needed(producto)
        producto.refresh_from_db()
        self.assertEqual(producto.reserved_boxes, [{"code": "b-2", "units": 1}])

    def test_cajas_completas_y_fraccion(self):
        caja = self.crear_caja([("b-1", 10), ("b-2", 10), ("b-3", 3)])
        producto = self.crear_producto(caja, amount=1.5)
        functions._allocate_boxes_if_needed(producto)
        producto.refresh_from_db()
        self.assertEqual(
            producto.reserved_boxes, [{"code": "b-1", "units": 10}, {"code": "b-2", "units": 5}]
        )

    def test_fraccion_sin_caja_suficiente_solo_asigna_completas(self):
        caja = self.crear_caja([("b-1", 10), ("b-3", 2)])
        producto = self.crear_producto(caja, amount=1.5)
        functions._allocate_boxes_if_needed(producto)
        producto.refresh_from_db()
        self.assertEqual(producto.reserved_boxes, [{"code": "b-1", "units": 10}])


class TareaDeDescuentoTest(ReservationsBaseTest):
    def test_reprogramar_revoca_la_tarea_anterior(self):
        producto = self.crear_producto(self.crear_objeto_estante())
        tarea = ReservationTasks.objects.create(reserved_product=producto, task_type="decrease")
        with mock.patch.object(functions.app.control, "revoke") as revoke:
            functions.add_decrease_stock_task(producto)
        revoke.assert_any_call(tarea.celery_task, terminate=True)
        self.assertFalse(ReservationTasks.objects.filter(pk=tarea.pk).exists())
        periodica = PeriodicTask.objects.get(name=f"decrease_stock_{producto.pk}")
        self.assertEqual(json.loads(periodica.args), [producto.pk])
        self.assertTrue(periodica.one_off)

    def test_fecha_ingenua_se_vuelve_consciente(self):
        producto = SimpleNamespace(id=987654, initial_date=datetime(2030, 1, 1, 8, 0))
        functions.schedule_decrease_stock(producto)
        periodica = PeriodicTask.objects.get(name="decrease_stock_987654")
        self.assertIsNotNone(periodica.clocked.clocked_time.tzinfo)
