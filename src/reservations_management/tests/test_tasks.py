from django_celery_beat.models import ClockedSchedule, PeriodicTask
from djgentelella.models import Notification

from laboratory.models import ShelfObjectObservation
from reservations_management.models import BORROWED, DENIED, REQUESTED
from reservations_management.tasks import _find_replacement_boxes, decrease_stock
from reservations_management.tests.base import ReservationsBaseTest


class DescontarStockTest(ReservationsBaseTest):
    """La tarea `decrease_stock` que Celery beat dispara al iniciar la reserva."""

    def programar(self, pk):
        clocked = ClockedSchedule.objects.create(clocked_time=self.ahora)
        PeriodicTask.objects.create(
            clocked=clocked,
            name=f"decrease_stock_{pk}",
            task="reservations_management.tasks.decrease_stock",
            one_off=True,
        )

    def assertTareaBorrada(self, pk):
        self.assertFalse(PeriodicTask.objects.filter(name=f"decrease_stock_{pk}").exists())

    def test_producto_inexistente_solo_limpia_la_tarea(self):
        self.programar(987654)
        decrease_stock(987654)
        self.assertTareaBorrada(987654)

    def test_reserva_vencida_se_niega(self):
        producto = self.crear_producto(self.crear_objeto_estante(), inicio=-5, fin=-1, status=REQUESTED)
        self.programar(producto.pk)
        decrease_stock(producto.pk)
        producto.refresh_from_db()
        self.assertEqual(producto.status, DENIED)
        self.assertTareaBorrada(producto.pk)

    def test_descuento_estandar(self):
        objeto = self.crear_objeto_estante(quantity=10)
        producto = self.crear_producto(objeto, amount=4, inicio=0)
        decrease_stock(producto)
        objeto.refresh_from_db()
        self.assertEqual(objeto.quantity, 6)

    def test_descuento_estandar_no_queda_negativo(self):
        objeto = self.crear_objeto_estante(quantity=10)
        producto = self.crear_producto(objeto, amount=15, inicio=0)
        decrease_stock(producto.pk)
        objeto.refresh_from_db()
        self.assertEqual(objeto.quantity, 0)


class DescontarCajasTest(ReservationsBaseTest):
    def producto(self, cajas_reservadas, cajas=None):
        caja = self.crear_caja(cajas)
        return self.crear_producto(caja, amount=1, inicio=0, reserved_boxes=cajas_reservadas)

    def unidades(self, producto):
        producto.shelf_object.refresh_from_db()
        return {b["code"]: (b["units"], b["quantity"]) for b in producto.shelf_object.quantity_units}

    def test_descuenta_y_elimina_cajas_vacias(self):
        producto = self.producto([{"code": "b-1", "units": 4}, {"code": "b-2", "units": 10}])
        decrease_stock(producto.pk)
        self.assertEqual(self.unidades(producto), {"b-1": (6, 6)})
        producto.refresh_from_db()
        self.assertEqual(producto.status, BORROWED)
        self.assertTrue(ShelfObjectObservation.objects.filter(shelf_object=producto.shelf_object).exists())

    def test_descuento_con_unidad_en_estante(self):
        self.usar_unidad_en_estante()
        producto = self.producto([{"code": "b-1", "units": 4}])
        decrease_stock(producto.pk)
        self.assertEqual(self.unidades(producto), {"b-1": (6, 6), "b-2": (10, 10)})

    def test_caja_desaparecida_se_reemplaza(self):
        producto = self.producto([{"code": "b-9", "units": 5}], cajas=[("b-1", 10)])
        decrease_stock(producto.pk)
        producto.refresh_from_db()
        self.assertEqual(producto.reserved_boxes, [{"code": "b-1", "units": 5}])
        self.assertEqual(self.unidades(producto), {"b-1": (5, 5)})
        self.assertEqual(producto.status, BORROWED)

    def test_sin_stock_para_reemplazar_se_niega_y_notifica(self):
        producto = self.producto([{"code": "b-9", "units": 50}], cajas=[("b-1", 10)])
        decrease_stock(producto.pk)
        producto.refresh_from_db()
        self.assertEqual(producto.status, DENIED)
        self.assertEqual(self.unidades(producto), {"b-1": (10, 10)})
        self.assertTrue(Notification.objects.filter(user=self.user, message_type="warning").exists())

    def test_reemplazo_salta_las_cajas_ya_reservadas(self):
        reemplazos, faltante = _find_replacement_boxes(
            12, {"b-1": 10, "b-2": 10, "b-3": 10, "b-4": 10}, {"b-1"}
        )
        self.assertEqual(reemplazos, [{"code": "b-2", "units": 10}, {"code": "b-3", "units": 2}])
        self.assertEqual(faltante, 0)
