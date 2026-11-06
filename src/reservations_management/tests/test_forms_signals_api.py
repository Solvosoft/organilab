from unittest import mock
from urllib.parse import urlencode

from django.urls import reverse
from django_celery_beat.models import PeriodicTask

from reservations_management import signals
from reservations_management.forms import ReturnProductForm
from reservations_management.models import (
    BORROWED,
    REQUESTED,
    ReservationTasks,
    ReservedProducts,
)
from reservations_management.tests.base import ReservationsBaseTest


class FormularioDevolucionTest(ReservationsBaseTest):
    def test_sin_producto_no_valida_nada_extra(self):
        form = ReturnProductForm(data={})
        self.assertTrue(form.is_valid())

    def test_producto_en_cajas_exige_cajas(self):
        producto = self.crear_producto(
            self.crear_caja(), amount=1, reserved_boxes=[{"code": "b-1", "units": 4}]
        )
        form = ReturnProductForm(data={}, product=producto)
        self.assertNotIn("amount_returned", form.fields)
        self.assertEqual([c[0] for c in form.fields["reserved_boxes"].choices], ["b-1"])
        self.assertFalse(form.is_valid())
        self.assertTrue(ReturnProductForm(data={"reserved_boxes": ["b-1"]}, product=producto).is_valid())

    def test_producto_estandar_valida_la_cantidad(self):
        producto = self.crear_producto(self.crear_objeto_estante(), amount=10)
        form = ReturnProductForm(data={"amount_returned": 0}, product=producto)
        self.assertNotIn("reserved_boxes", form.fields)
        self.assertFalse(form.is_valid())
        self.assertFalse(ReturnProductForm(data={"amount_returned": 11}, product=producto).is_valid())
        self.assertTrue(ReturnProductForm(data={"amount_returned": 5}, product=producto).is_valid())


class SenalesTest(ReservationsBaseTest):
    def test_borrar_producto_borra_y_revoca_sus_tareas(self):
        producto = self.crear_producto(self.crear_objeto_estante())
        tarea = ReservationTasks.objects.create(reserved_product=producto, task_type="decrease")
        with mock.patch.object(signals.app.control, "revoke") as revoke:
            producto.delete()
        revoke.assert_called_with(tarea.celery_task, terminate=True)
        self.assertFalse(ReservationTasks.objects.filter(pk=tarea.pk).exists())

    def test_error_al_buscar_tareas_no_impide_borrar(self):
        producto = self.crear_producto(self.crear_objeto_estante())
        with mock.patch.object(signals.ReservationTasks.objects, "filter", side_effect=RuntimeError):
            producto.delete()
        self.assertFalse(ReservedProducts.objects.filter(pk=producto.pk).exists())


class ApiProductoReservadoTest(ReservationsBaseTest):
    def url(self, pk):
        return reverse("api_reservation_management", kwargs={"pk": pk})

    def formulario(self, producto, **cambios):
        datos = {
            "shelf_object": producto.shelf_object_id,
            "amount_required": producto.amount_required,
            "initial_date": producto.initial_date.isoformat(),
            "final_date": producto.final_date.isoformat(),
            "status": "1",
            "reserved_boxes": "[]",
        }
        datos.update(cambios)
        return urlencode(datos)

    def enviar(self, metodo, producto, **cambios):
        return getattr(self.client, metodo)(
            self.url(producto.pk),
            self.formulario(producto, **cambios),
            content_type="application/x-www-form-urlencoded",
        )

    def test_anonimo_no_tiene_acceso(self):
        producto = self.crear_producto(self.crear_objeto_estante())
        self.client.logout()
        self.assertIn(self.client.get(self.url(producto.pk)).status_code, (401, 403))
        listado = reverse("api_reservation_products_list", kwargs={"pk": self.reservacion.pk})
        self.assertIn(self.client.get(listado).status_code, (401, 403))

    def test_consultar_producto(self):
        producto = self.crear_producto(self.crear_objeto_estante(), amount=7)
        respuesta = self.client.get(self.url(producto.pk))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["amount_required"], 7)

    def test_producto_inexistente_es_404(self):
        self.assertEqual(self.client.get(self.url(987654)).status_code, 404)

    def test_listar_productos_de_la_reservacion(self):
        producto = self.crear_producto(self.crear_objeto_estante())
        respuesta = self.client.get(
            reverse("api_reservation_products_list", kwargs={"pk": self.reservacion.pk})
        )
        self.assertEqual([p["id"] for p in respuesta.json()], [producto.pk])

    def test_put_aceptar_futuro_programa_el_descuento(self):
        producto = self.crear_producto(self.crear_objeto_estante(), status=REQUESTED)
        respuesta = self.enviar("put", producto)
        self.assertEqual(respuesta.status_code, 200)
        producto.refresh_from_db()
        self.assertEqual(producto.status, BORROWED)
        self.assertTrue(PeriodicTask.objects.filter(name=f"decrease_stock_{producto.pk}").exists())

    def test_put_aceptar_ya_iniciado_descuenta_de_inmediato(self):
        objeto = self.crear_objeto_estante(quantity=50)
        producto = self.crear_producto(objeto, amount=10, inicio=-1, status=REQUESTED)
        self.assertEqual(self.enviar("put", producto).status_code, 200)
        objeto.refresh_from_db()
        self.assertEqual(objeto.quantity, 40)

    def test_put_invalido(self):
        producto = self.crear_producto(self.crear_objeto_estante(), status=REQUESTED)
        self.assertEqual(self.enviar("put", producto, amount_required="x").status_code, 400)

    def test_patch_aceptar_futuro_programa_el_descuento(self):
        producto = self.crear_producto(self.crear_objeto_estante(), status=REQUESTED)
        respuesta = self.client.patch(
            self.url(producto.pk), urlencode({"status": "1"}),
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(PeriodicTask.objects.filter(name=f"decrease_stock_{producto.pk}").exists())

    def test_patch_aceptar_ya_iniciado_descuenta_de_inmediato(self):
        objeto = self.crear_objeto_estante(quantity=50)
        producto = self.crear_producto(objeto, amount=10, inicio=-1, status=REQUESTED)
        self.client.patch(
            self.url(producto.pk), urlencode({"status": "1"}),
            content_type="application/x-www-form-urlencoded",
        )
        objeto.refresh_from_db()
        self.assertEqual(objeto.quantity, 40)

    def test_patch_invalido(self):
        producto = self.crear_producto(self.crear_objeto_estante(), status=REQUESTED)
        respuesta = self.client.patch(
            self.url(producto.pk), urlencode({"status": "zz"}),
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(respuesta.status_code, 400)
