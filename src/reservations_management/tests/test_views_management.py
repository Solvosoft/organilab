import json

from django.urls import reverse
from django_celery_beat.models import PeriodicTask

from reservations_management.models import (
    BORROWED,
    CLOSED,
    DENIED,
    REQUESTED,
    RETURNED,
    Reservations,
)
from reservations_management.tests.base import ReservationsBaseTest


class GestionarReservacionTest(ReservationsBaseTest):
    def url(self):
        return reverse(
            "reservations_management:manage_reservation",
            kwargs={"org_pk": 1, "pk": self.reservacion.pk},
        )

    def test_aceptar_presta_los_vigentes_y_niega_los_vencidos(self):
        vigente = self.crear_producto(self.crear_caja(), amount=1, status=REQUESTED)
        vencido = self.crear_producto(self.crear_objeto_estante(), inicio=-5, fin=-1, status=REQUESTED)
        respuesta = self.client.post(self.url(), {"comments": "ok", "action": "accept"})
        self.assertEqual(respuesta.status_code, 302)
        vigente.refresh_from_db()
        vencido.refresh_from_db()
        self.assertEqual(vigente.status, BORROWED)
        self.assertEqual(vigente.reserved_boxes, [{"code": "b-1", "units": 10}])
        self.assertTrue(PeriodicTask.objects.filter(name=f"decrease_stock_{vigente.pk}").exists())
        self.assertEqual(vencido.status, DENIED)
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.comments, "ok")

    def test_rechazar_niega_lo_no_prestado(self):
        pedido = self.crear_producto(self.crear_objeto_estante(), status=REQUESTED)
        prestado = self.crear_producto(self.crear_objeto_estante(), status=BORROWED)
        devuelto = self.crear_producto(self.crear_objeto_estante(), status=RETURNED)
        self.client.post(self.url(), {"comments": "no", "action": "reject"})
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.status, DENIED)
        estados = {p.pk: p.status for p in self.reservacion.reservedproducts_set.all()}
        self.assertEqual(estados[pedido.pk], DENIED)
        self.assertEqual(estados[prestado.pk], BORROWED)
        self.assertEqual(estados[devuelto.pk], RETURNED)


class AccionSobreProductoTest(ReservationsBaseTest):
    def accion(self, producto, accion, reservacion=None):
        return self.client.post(
            reverse(
                "reservations_management:product_action",
                kwargs={
                    "org_pk": 1,
                    "pk": (reservacion or self.reservacion).pk,
                    "product_pk": producto.pk,
                },
            ),
            {"action": accion},
        )

    def test_aceptar_producto_vigente(self):
        producto = self.crear_producto(self.crear_objeto_estante(), status=REQUESTED)
        respuesta = self.accion(producto, "accept")
        self.assertRedirects(
            respuesta,
            reverse(
                "reservations_management:manage_reservation",
                kwargs={"org_pk": 1, "pk": self.reservacion.pk},
            ),
            fetch_redirect_response=False,
        )
        producto.refresh_from_db()
        self.assertEqual(producto.status, BORROWED)
        self.assertTrue(PeriodicTask.objects.filter(name=f"decrease_stock_{producto.pk}").exists())

    def test_aceptar_producto_vencido_lo_niega(self):
        producto = self.crear_producto(self.crear_objeto_estante(), inicio=-5, fin=-1, status=REQUESTED)
        self.accion(producto, "accept")
        producto.refresh_from_db()
        self.assertEqual(producto.status, DENIED)

    def test_rechazar_producto(self):
        producto = self.crear_producto(self.crear_objeto_estante(), status=REQUESTED)
        self.accion(producto, "reject")
        producto.refresh_from_db()
        self.assertEqual(producto.status, DENIED)

    def test_producto_no_solicitado_no_cambia(self):
        producto = self.crear_producto(self.crear_objeto_estante(), status=RETURNED)
        self.accion(producto, "reject")
        producto.refresh_from_db()
        self.assertEqual(producto.status, RETURNED)

    def test_producto_de_otra_reservacion_es_404(self):
        producto = self.crear_producto(self.crear_objeto_estante(), status=REQUESTED)
        otra = Reservations.objects.create(user=self.user)
        respuesta = self.accion(producto, "accept", reservacion=otra)
        self.assertRedirects(respuesta, reverse("error_view") + "?status=404", fetch_redirect_response=False)
        producto.refresh_from_db()
        self.assertEqual(producto.status, REQUESTED)


class DevolverProductoTest(ReservationsBaseTest):
    def devolver(self, producto, datos):
        return self.client.post(
            reverse(
                "reservations_management:return_product",
                kwargs={"org_pk": 1, "pk": self.reservacion.pk, "product_pk": producto.pk},
            ),
            datos,
        ).json()

    def producto_en_cajas(self):
        return self.crear_producto(
            self.crear_caja(), amount=1, inicio=-1, reserved_boxes=[{"code": "b-1", "units": 4}]
        )

    def assertError(self, datos):
        self.assertFalse(datos["success"])
        self.assertIn("error", datos)

    def test_antes_de_iniciar_no_se_devuelve(self):
        producto = self.crear_producto(self.crear_objeto_estante())
        self.assertError(self.devolver(producto, {"amount_returned": 1}))

    def test_cajas_json_invalido(self):
        self.assertError(self.devolver(self.producto_en_cajas(), {"boxes_to_return": "{x"}))

    def test_cajas_sin_seleccion(self):
        self.assertError(self.devolver(self.producto_en_cajas(), {"boxes_to_return": "[]"}))

    def test_caja_no_reservada(self):
        datos = {"boxes_to_return": json.dumps([{"code": "b-9", "units": 1}])}
        self.assertError(self.devolver(self.producto_en_cajas(), datos))

    def test_unidades_negativas(self):
        datos = {"boxes_to_return": json.dumps([{"code": "b-1", "units": -1}])}
        self.assertError(self.devolver(self.producto_en_cajas(), datos))

    def test_unidades_mayores_a_las_reservadas(self):
        datos = {"boxes_to_return": json.dumps([{"code": "b-1", "units": 5}])}
        self.assertError(self.devolver(self.producto_en_cajas(), datos))

    def test_devolucion_de_cajas(self):
        producto = self.producto_en_cajas()
        datos = {"boxes_to_return": json.dumps([{"code": "b-1", "units": 4}])}
        self.assertEqual(self.devolver(producto, datos), {"success": True})
        producto.refresh_from_db()
        self.assertEqual(producto.status, RETURNED)

    def test_cantidad_no_numerica(self):
        producto = self.crear_producto(self.crear_objeto_estante(), inicio=-1)
        self.assertError(self.devolver(producto, {"amount_returned": "abc"}))

    def test_cantidad_fuera_de_rango(self):
        producto = self.crear_producto(self.crear_objeto_estante(), inicio=-1)
        self.assertError(self.devolver(producto, {"amount_returned": 11}))

    def test_devolucion_estandar(self):
        objeto = self.crear_objeto_estante(quantity=50)
        producto = self.crear_producto(objeto, inicio=-1)
        self.assertEqual(self.devolver(producto, {"amount_returned": 4}), {"success": True})
        objeto.refresh_from_db()
        producto.refresh_from_db()
        self.assertEqual(objeto.quantity, 54)
        self.assertEqual(producto.amount_returned, 4)
        self.assertEqual(producto.status, RETURNED)


class CerrarReservacionTest(ReservationsBaseTest):
    def test_cerrar_reservacion(self):
        respuesta = self.client.post(
            reverse(
                "reservations_management:close_reservation",
                kwargs={"org_pk": 1, "pk": self.reservacion.pk},
            )
        )
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.status, CLOSED)
        self.assertRedirects(
            respuesta,
            reverse(
                "reservations_management:reservations_list",
                kwargs={"org_pk": 1, "status": CLOSED},
            ),
            fetch_redirect_response=False,
        )
