"""Devolución de productos: valores numéricos que no son cantidades."""

from django.urls import reverse

from reservations_management.models import BORROWED
from reservations_management.tests.base import ReservationsBaseTest


class DevolucionConCantidadNoFinitaTest(ReservationsBaseTest):
    def devolver(self, producto, cantidad):
        return self.client.post(
            reverse(
                "reservations_management:return_product",
                kwargs={"org_pk": 1, "pk": self.reservacion.pk, "product_pk": producto.pk},
            ),
            {"amount_returned": cantidad},
        ).json()

    def test_nan_se_rechaza_y_no_toca_el_inventario(self):
        """`float("nan")` no es < 0 ni > máximo: antes pasaba la validación y dejaba la
        cantidad del objeto en NaN."""
        objeto = self.crear_objeto_estante(quantity=50)
        producto = self.crear_producto(objeto, inicio=-1)
        datos = self.devolver(producto, "nan")
        self.assertFalse(datos["success"])
        objeto.refresh_from_db()
        producto.refresh_from_db()
        self.assertEqual(objeto.quantity, 50)
        self.assertEqual(producto.status, BORROWED)
        self.assertEqual(producto.amount_returned, 0)

    def test_infinito_se_rechaza(self):
        producto = self.crear_producto(self.crear_objeto_estante(), inicio=-1)
        self.assertFalse(self.devolver(producto, "inf")["success"])
        producto.refresh_from_db()
        self.assertEqual(producto.status, BORROWED)
