# encoding: utf-8
"""Vistas heredadas de ``laboratory/views/shelfobject.py``.

Son las rutas AJAX previas al labview (``lab/<org>/<lab>/shelfobject/...``),
la descarga del QR, el detalle de equipo y la etiqueta SGA de una instancia.
Además del camino feliz se prueba el aislamiento: un objeto de estante de otro
laboratorio no se puede ver, editar ni borrar a través del laboratorio propio.
"""

import json
from unittest import mock

from django.contrib.auth.models import Permission
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.urls import reverse

from laboratory.models import (
    Laboratory,
    LaboratoryRoom,
    OrganizationStructure,
    Shelf,
    ShelfObject,
    ShelfObjectEquipmentCharacteristics,
)
from laboratory.tests.utils import BaseLaboratorySetUpTest
from presentation.models import QRModel
from sga.models import RecipientSize

AJAX = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


class BaseShelfObjectLegacyTest(BaseLaboratorySetUpTest):
    """Laboratorio propio (org 1 / lab 1) y un objeto de estante ajeno."""

    def setUp(self):
        super().setUp()
        self.shelfobject = ShelfObject.objects.get(pk=1)
        # La sala 2 pasa a un laboratorio de otra organización: sus estantes y
        # lo que contengan dejan de pertenecer al laboratorio de la URL.
        self.org_ajena = OrganizationStructure.objects.create(name="Org ajena")
        self.lab_ajeno = Laboratory.objects.create(
            name="Lab ajeno", organization=self.org_ajena
        )
        LaboratoryRoom.objects.filter(pk=2).update(laboratory=self.lab_ajeno)
        self.shelf_ajeno = Shelf.objects.get(pk=10)
        self.so_ajeno = ShelfObject.objects.create(
            shelf=self.shelf_ajeno,
            object_id=1,
            quantity=3,
            limit_quantity=1,
            measurement_unit_id=63,
            in_where_laboratory=self.lab_ajeno,
        )

    def url(self, name, **kwargs):
        kwargs.update({"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        return reverse("laboratory:" + name, kwargs=kwargs)

    def ajax_get(self, url, data=None):
        return self.client.get(url, data or {}, **AJAX).json()

    def ajax_post(self, url, data=None):
        return self.client.post(url, data or {}, **AJAX).json()


class ListShelfObjectTest(BaseShelfObjectLegacyTest):

    def test_lista_objetos_del_estante(self):
        data = self.ajax_get(self.url("list_shelfobject"), {"shelf": 1})
        self.assertEqual(data["status"], 200)
        fragmentos = data["content"]["inner-fragments"]
        self.assertEqual(fragmentos["#shelfposition"], "1")
        self.assertIn("shelfobject_view_%d" % self.shelfobject.pk, fragmentos["#shelfobject"])

    def test_sin_cabecera_ajax_responde_400(self):
        response = self.client.get(self.url("list_shelfobject"), {"shelf": 1})
        self.assertEqual(response.status_code, 400)

    def test_estante_inexistente_o_ajeno_da_404(self):
        for shelf in ["", "0", "abc", self.shelf_ajeno.pk]:
            with self.subTest(shelf=shelf):
                data = self.ajax_get(self.url("list_shelfobject"), {"shelf": shelf})
                self.assertEqual(data["status"], 404)


class ShelfObjectCreateTest(BaseShelfObjectLegacyTest):

    def post_data(self, shelf, **extra):
        data = {
            "shelf": shelf,
            "objecttype": "0",
            "object": 1,
            "batch": "L-1",
            "quantity": 5,
            "quantity_base_unit": 0,
            "limit_quantity": 1,
            "measurement_unit": 63,
            "concentration": 0,
            "quantity_units": json.dumps([{"code": "b-0001", "units": 1}]),
            "units_per_box": 0,
        }
        data.update(extra)
        return data

    def test_formulario_segun_tipo_de_estante(self):
        data = self.ajax_get(self.url("shelfobject_create"), {"shelf": 1, "objecttype": "0"})
        self.assertEqual(data["status"], 200)
        self.assertIn("id_measurement_unit", data["content"])
        # Estante de desecho: formulario de desecho, marcado como descarte.
        data = self.ajax_get(self.url("shelfobject_create"), {"shelf": 5, "objecttype": "0"})
        self.assertEqual(data["status"], 200)
        self.assertIn("marked_as_discard", data["content"])

    def test_crea_objeto_con_qr_y_bitacora(self):
        total = ShelfObject.objects.count()
        data = self.ajax_post(self.url("shelfobject_create"), self.post_data(2))
        self.assertEqual(data["status"], 200, data)
        self.assertIn("#closemodal", data["content"]["inner-fragments"])
        self.assertEqual(ShelfObject.objects.count(), total + 1)
        nuevo = ShelfObject.objects.latest("pk")
        self.assertEqual(nuevo.created_by, self.user)
        self.assertEqual(nuevo.in_where_laboratory_id, self.lab.pk)
        self.assertIn("shelfobject=%d" % nuevo.pk, nuevo.shelf_object_url)
        self.assertTrue(nuevo.shelf_object_qr)

    def test_unidad_y_cantidad_del_estante(self):
        url = self.url("shelfobject_create")
        # Misma unidad que el estante y dentro del límite.
        data = self.ajax_post(url, self.post_data(1))
        self.assertIn("#closemodal", data["content"]["inner-fragments"])
        # Unidad distinta a la del estante.
        data = self.ajax_post(url, self.post_data(1, measurement_unit=59))
        self.assertIn("#shelfobjectCreate", data["content"]["inner-fragments"])
        # Estante con capacidad 40: 50 unidades no caben.
        data = self.ajax_post(url, self.post_data(13, measurement_unit=59, quantity=50))
        self.assertIn("#shelfobjectCreate", data["content"]["inner-fragments"])

    def test_estante_de_desecho(self):
        url = self.url("shelfobject_create")
        shelf = Shelf.objects.get(pk=5)
        # Sin unidad ni capacidad: acepta y lo marca como descarte.
        data = self.ajax_post(url, self.post_data(5, marked_as_discard=True))
        self.assertIn("#closemodal", data["content"]["inner-fragments"])
        self.assertTrue(ShelfObject.objects.latest("pk").marked_as_discard)
        # Capacidad excedida.
        shelf.quantity = 1
        shelf.measurement_unit_id = 63
        shelf.save()
        data = self.ajax_post(url, self.post_data(5, quantity=10))
        self.assertIn("#shelfobjectCreate", data["content"]["inner-fragments"])
        # Unidad distinta.
        data = self.ajax_post(url, self.post_data(5, quantity=1, measurement_unit=59))
        self.assertIn("#shelfobjectCreate", data["content"]["inner-fragments"])


class ShelfObjectEditTest(BaseShelfObjectLegacyTest):

    def edit_data(self, **extra):
        data = {
            "shelf": 1,
            "objecttype": "0",
            "quantity": 10,
            "limit_quantity": 2,
            "measurement_unit": 63,
            "row": 0,
            "col": 1,
        }
        data.update(extra)
        return data

    def test_formulario_de_edicion(self):
        url = self.url("shelfobject_edit", pk=self.shelfobject.pk)
        data = self.ajax_get(url, {"shelf": 1, "objecttype": "0", "row": 0, "col": 1})
        self.assertEqual(data["status"], 200, data)
        self.assertIn("id_quantity", data["content"])

    def test_edita_cantidad(self):
        url = self.url("shelfobject_edit", pk=self.shelfobject.pk)
        data = self.ajax_post(url, self.edit_data())
        self.assertEqual(data["status"], 200, data)
        self.assertIn("#row_0_col_1_shelf_1", data["content"]["inner-fragments"])
        self.shelfobject.refresh_from_db()
        self.assertEqual(self.shelfobject.quantity, 10)

    def test_objeto_de_otro_laboratorio_da_404(self):
        url = self.url("shelfobject_edit", pk=self.so_ajeno.pk)
        data = self.ajax_post(url, self.edit_data(shelf=self.shelf_ajeno.pk))
        self.assertEqual(data["status"], 404)
        self.so_ajeno.refresh_from_db()
        self.assertEqual(self.so_ajeno.quantity, 3)


class ShelfObjectSearchUpdateTest(BaseShelfObjectLegacyTest):

    def test_formulario_en_busqueda(self):
        url = self.url("shelfobject_searchupdate", pk=self.shelfobject.pk)
        data = self.ajax_get(url)
        self.assertEqual(data["status"], 200, data)
        fragmento = data["content"]["inner-fragments"]["#o%d" % self.shelfobject.pk]
        self.assertIn("q/update/%d/" % self.shelfobject.pk, fragmento)

    def test_actualiza_y_renderiza_el_objeto(self):
        url = self.url("shelfobject_searchupdate", pk=self.shelfobject.pk)
        data = self.ajax_post(
            url,
            {"shelf": 1, "quantity": 7, "limit_quantity": 1, "measurement_unit": 63},
        )
        self.assertEqual(data["status"], 200, data)
        self.assertIn("#o%d" % self.shelfobject.pk, data["content"]["inner-fragments"])
        self.shelfobject.refresh_from_db()
        self.assertEqual(self.shelfobject.quantity, 7)

    def test_formulario_invalido_vuelve_a_mostrarse(self):
        url = self.url("shelfobject_searchupdate", pk=self.shelfobject.pk)
        data = self.ajax_post(url, {"shelf": 1, "quantity": "x"})
        fragmento = data["content"]["inner-fragments"]["#o%d" % self.shelfobject.pk]
        self.assertIn("id_quantity", fragmento)
        self.shelfobject.refresh_from_db()
        self.assertEqual(self.shelfobject.quantity, 23)

    def test_objeto_de_otro_laboratorio_da_404(self):
        url = self.url("shelfobject_searchupdate", pk=self.so_ajeno.pk)
        self.assertEqual(self.ajax_get(url)["status"], 404)


class ShelfObjectDeleteTest(BaseShelfObjectLegacyTest):

    def test_con_reservas_activas_no_se_borra(self):
        url = self.url("shelfobject_delete", pk=self.shelfobject.pk)
        data = self.ajax_post(url)
        self.assertIn("Swal.fire", data["content"]["inner-fragments"]["#closemodal"])
        self.assertTrue(ShelfObject.objects.filter(pk=self.shelfobject.pk).exists())

    def test_borra_objeto_sin_reservas(self):
        url = self.url("shelfobject_delete", pk=2)
        data = self.ajax_post(url)
        self.assertNotIn("Swal.fire", data["content"]["inner-fragments"]["#closemodal"])
        self.assertFalse(ShelfObject.objects.filter(pk=2).exists())

    def test_objeto_de_otro_laboratorio_da_404(self):
        url = self.url("shelfobject_delete", pk=self.so_ajeno.pk)
        self.assertEqual(self.ajax_post(url)["status"], 404)
        self.assertTrue(ShelfObject.objects.filter(pk=self.so_ajeno.pk).exists())


class ShelfObjectDetailScopeTest(BaseShelfObjectLegacyTest):

    def test_objeto_de_otro_laboratorio_da_404(self):
        url = self.url("shelfobject_detail", pk=self.so_ajeno.pk)
        self.assertEqual(self.ajax_get(url)["status"], 404)


class EditLimitObjectTest(BaseShelfObjectLegacyTest):

    def test_consulta_y_guarda_limite(self):
        url = self.url("get_shelfobject_limit", pk=self.shelfobject.pk)
        response = self.client.get(url)
        self.assertEqual(response.json()["amount"], 7.0)
        response = self.client.post(url, {"amount": "4.5"})
        self.assertEqual(response.json()["msg"], "Se guardo correctamente")
        self.shelfobject.refresh_from_db()
        self.assertEqual(self.shelfobject.limit_quantity, 4.5)

    def test_objeto_de_otro_laboratorio_da_404(self):
        url = self.url("get_shelfobject_limit", pk=self.so_ajeno.pk)
        response = self.client.post(url, {"amount": "99"})
        self.assertNegado(response, 404)
        self.so_ajeno.refresh_from_db()
        self.assertEqual(self.so_ajeno.limit_quantity, 1)


class DownloadShelfObjectQRTest(BaseShelfObjectLegacyTest):

    def crear_qr(self):
        detail = self.url("equipment_shelfobject_detail", pk=self.shelfobject.pk)
        self.assertEqual(self.client.get(detail).status_code, 200)
        return QRModel.objects.get(object_id=self.shelfobject.pk, organization=self.org)

    def test_descarga_el_svg(self):
        self.crear_qr()
        response = self.client.get(self.url("download_shelfobject_qr", pk=self.shelfobject.pk))
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'filename="shelfobject_%d.svg"' % self.shelfobject.pk,
            response["Content-Disposition"],
        )

    def test_sin_qr_da_404(self):
        response = self.client.get(self.url("download_shelfobject_qr", pk=self.shelfobject.pk))
        self.assertNegado(response, 404)

    def test_qr_sin_imagen_da_404(self):
        qr = self.crear_qr()
        qr.qr_image = ""
        qr.save()
        response = self.client.get(self.url("download_shelfobject_qr", pk=self.shelfobject.pk))
        self.assertNegado(response, 404)


class EquipmentDetailTest(BaseShelfObjectLegacyTest):

    def test_equipo_con_caracteristicas(self):
        self.assertTrue(ShelfObjectEquipmentCharacteristics.objects.filter(shelfobject_id=15).exists())
        response = self.client.get(self.url("equipment_shelfobject_detail", pk=15))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["edit_form"].instance.shelfobject_id, 15)

    def test_objeto_de_otro_laboratorio_da_404(self):
        response = self.client.get(self.url("equipment_shelfobject_detail", pk=self.so_ajeno.pk))
        self.assertNegado(response, 404)
        self.assertFalse(QRModel.objects.filter(object_id=self.so_ajeno.pk).exists())


class ShelfObjectLabelTest(BaseShelfObjectLegacyTest):

    def setUp(self):
        super().setUp()
        self.recipient = RecipientSize.objects.create(name="Frasco", height=10, width=10)

    def test_genera_etiqueta_con_ajustes(self):
        url = reverse(
            "laboratory:generate_shelfobject_label",
            kwargs={
                "org_pk": self.org.pk,
                "lab_pk": self.lab.pk,
                "pk": self.shelfobject.pk,
                "recipient": self.recipient.pk,
            },
        )
        with mock.patch(
            "sga.label_render.render_label", return_value=HttpResponse("ok")
        ) as render, mock.patch(
            "sga.label_blueprint.blueprint_from_shelfobject", return_value="bp"
        ) as blueprint:
            response = self.client.get(
                url,
                {
                    "lote": "L9",
                    "fecha_caducidad": "2030-01-01",
                    "cantidad": "5 g",
                    "qr_url": "http://x",
                    "ancho_mm": "50",
                    "alto_mm": "30",
                    "formato": "svg",
                },
            )
        self.assertEqual(response.status_code, 200)
        kwargs = blueprint.call_args.kwargs
        self.assertEqual(kwargs["lote"], "L9")
        self.assertEqual(kwargs["ancho_mm"], 50.0)
        self.assertEqual(kwargs["alto_mm"], 30.0)
        self.assertEqual(render.call_args.args[1], "svg")

    def test_etiqueta_png_real(self):
        url = reverse(
            "laboratory:generate_shelfobject_label",
            kwargs={
                "org_pk": self.org.pk,
                "lab_pk": self.lab.pk,
                "pk": self.shelfobject.pk,
                "recipient": self.recipient.pk,
            },
        )
        response = self.client.get(url)
        self.assertIn(response.status_code, (200, 400))

    def test_objeto_de_otro_laboratorio_da_404(self):
        url = reverse(
            "laboratory:generate_shelfobject_label",
            kwargs={
                "org_pk": self.org.pk,
                "lab_pk": self.lab.pk,
                "pk": self.so_ajeno.pk,
                "recipient": self.recipient.pk,
            },
        )
        self.assertNegado(self.client.get(url), 404)
