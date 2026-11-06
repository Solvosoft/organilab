"""Carga de inventario desde la plantilla .xlsm (`laboratory.views.loadArchive`).

El archivo se arma en memoria con openpyxl y se sube como `ChunkedUpload`, igual que
lo deja el widget de subida por partes.
"""

import io
import json
from datetime import datetime

import openpyxl
from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils.timezone import now
from djgentelella.models import ChunkedUpload

from laboratory.models import (
    Catalog,
    Furniture,
    Laboratory,
    LaboratoryRoom,
    Object,
    OrganizationStructure,
    Shelf,
    ShelfObject,
    TemporalUploadReactive,
)
from laboratory.tests.utils import BaseLaboratorySetUpTest
from laboratory.views.loadArchive import DATA_START_ROW

FILA_ETANOL = [
    "Etanol", "64-17-5", "C2H6O", "Líquido", 10, "Mililitros", 100, "Mililitros",
    1, "Vidrio", 100, "Mililitros", datetime(2030, 1, 1),
]
FILA_ACETONA_SIN_UNIDAD = [
    "Acetona", "67-64-1", "C3H6O", "Seleccione", 5, "Seleccione", 50, "Mililitros",
    2, "Vidrio", None, None, "01-01-2030",
]


def assert_error_page(test, response, status):
    """`HandleErrorMiddleware` convierte 403/404 en redirección a la página de error."""
    test.assertEqual(response.status_code, 302)
    test.assertIn("status=%d" % status, response["Location"])


def xlsm_bytes(filas):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Formato de Iventario"
    for offset, fila in enumerate(filas):
        for col, valor in enumerate(fila, start=1):
            ws.cell(row=DATA_START_ROW + offset, column=col, value=valor)
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


class LoadArchiveBase(BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "laboratory:load_archive",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        self.mililitros = Catalog.objects.get(key="units", description="Mililitros")
        self.room = LaboratoryRoom.objects.create(name="Sala carga", laboratory=self.lab)
        self.furniture = Furniture.objects.create(
            labroom=self.room,
            name="Mueble carga",
            type=Catalog.objects.filter(key="furniture_type").first(),
        )
        self.shelf = self.crear_estante(self.furniture, None)

    def crear_estante(self, furniture, unidad):
        return Shelf.objects.create(
            furniture=furniture,
            name="Estante carga",
            type=Catalog.objects.filter(key="container_type").first(),
            measurement_unit=unidad,
        )

    def subir(self, filas, nombre="inventario.xlsm"):
        contenido = xlsm_bytes(filas)
        upload = ChunkedUpload.objects.create(
            file=ContentFile(contenido, name=nombre),
            filename=nombre,
            offset=len(contenido),
            completed_on=now(),
            user=self.user,
        )
        return json.dumps({"token": str(upload.upload_id)})

    def datos_con_lugar(self, shelf, filas):
        return {
            "create-file": self.subir(filas),
            "create-now_places": "on",
            "create-lab_room": shelf.furniture.labroom.pk,
            "create-furniture": shelf.furniture.pk,
            "create-shelf": shelf.pk,
        }


class LoadArchiveViewTest(LoadArchiveBase):

    def test_sin_lugar_crea_ubicacion_por_defecto_y_valida_el_archivo(self):
        # El widget de subida siempre envía el campo, vacío si no hay archivo.
        response = self.client.post(self.url, {"create-file": ""})
        self.assertEqual(response.status_code, 200)
        self.assertIn("file", response.context["errors"])
        self.assertTrue(response.context["create_form"].errors)
        shelf = Shelf.objects.get(
            name="Estante de Reactivos Cargados",
            furniture__labroom__laboratory=self.lab,
        )
        self.assertEqual(shelf.furniture.name, "Mueble de Reactivos Cargados")

    def test_archivo_valido_guarda_filas_temporales_y_redirige(self):
        data = self.datos_con_lugar(
            self.shelf, [FILA_ETANOL, [None] * 13, FILA_ACETONA_SIN_UNIDAD]
        )
        response = self.client.post(self.url, data)
        temp = TemporalUploadReactive.objects.get(shelf=self.shelf)
        self.assertRedirects(
            response,
            reverse(
                "laboratory:load_archive_create_shelfobjects",
                kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "key": temp.key},
            ),
            fetch_redirect_response=False,
        )
        # La fila vacía se salta y la acetona trae dos envases.
        self.assertEqual(
            [fila["nombre_producto"] for fila in temp.data],
            ["Etanol", "Acetona", "Acetona"],
        )
        self.assertEqual(temp.data[0]["fecha_caducidad"], "01-01-2030")
        self.assertIsNone(temp.data[1]["estado"])
        self.assertIsNone(temp.data[1]["unidades_cantidad"])

    def test_unidad_distinta_a_la_del_estante_muestra_error(self):
        shelf = self.crear_estante(
            self.furniture, Catalog.objects.get(key="units", description="Gramos")
        )
        response = self.client.post(
            self.url, self.datos_con_lugar(shelf, [FILA_ETANOL])
        )
        self.assertEqual(response.status_code, 200)
        mensajes = [str(m) for m in response.context["messages"]]
        self.assertEqual(len(mensajes), 1)
        self.assertIn("Gramos", mensajes[0])
        self.assertFalse(TemporalUploadReactive.objects.filter(shelf=shelf).exists())

    def test_fila_sin_unidad_en_estante_con_unidad_no_revienta(self):
        shelf = self.crear_estante(self.furniture, self.mililitros)
        response = self.client.post(
            self.url,
            self.datos_con_lugar(shelf, [FILA_ETANOL, FILA_ACETONA_SIN_UNIDAD]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(list(response.context["messages"])), 1)
        self.assertFalse(TemporalUploadReactive.objects.filter(shelf=shelf).exists())

    def test_estante_de_otro_laboratorio_responde_403(self):
        lab2 = Laboratory.objects.get(name="Lab Ultra")
        room = LaboratoryRoom.objects.create(name="Sala lab2", laboratory=lab2)
        furniture = Furniture.objects.create(
            labroom=room,
            name="Mueble lab2",
            type=Catalog.objects.filter(key="furniture_type").first(),
        )
        shelf = self.crear_estante(furniture, None)
        response = self.client.post(
            self.url, self.datos_con_lugar(shelf, [FILA_ETANOL])
        )
        assert_error_page(self, response, 403)
        self.assertFalse(TemporalUploadReactive.objects.exists())

    def test_laboratorio_fuera_de_la_organizacion_responde_403(self):
        otra_org = OrganizationStructure.objects.get(name="Organization Testing")
        lab_ajeno = Laboratory.objects.create(name="Lab ajeno", organization=otra_org)
        url = reverse(
            "laboratory:load_archive",
            kwargs={"org_pk": self.org.pk, "lab_pk": lab_ajeno.pk},
        )
        response = self.client.get(url)
        assert_error_page(self, response, 403)


class UploadReactivesViewTest(LoadArchiveBase):

    def setUp(self):
        super().setUp()
        self.temp = TemporalUploadReactive.objects.create(
            shelf=self.shelf,
            data=[{"nombre_producto": "Etanol", "shelf": self.shelf.pk}],
        )
        self.url = self.url_para(self.lab, self.temp)

    def url_para(self, lab, temp):
        return reverse(
            "laboratory:load_archive_create_shelfobjects",
            kwargs={"org_pk": self.org.pk, "lab_pk": lab.pk, "key": temp.key},
        )

    def fila(self, **extra):
        data = {
            "form-TOTAL_FORMS": 1,
            "form-INITIAL_FORMS": 0,
            "form-0-nombre_producto": "Etanol absoluto",
            "form-0-numero_cas": "64-17-5",
            "form-0-estado": "",
            "form-0-formula_quimica": "C2H6O",
            "form-0-cantidad": 10,
            "form-0-unidades_cantidad": "Mililitros",
            "form-0-capacidad_envase": 100,
            "form-0-unidades_capacidad": "Mililitros",
            "form-0-material_contenedor": "Botella vidrio",
            "form-0-cantidad_maxima_anual": 500,
            "form-0-unidades_cantidad_maxima": "Mililitros",
            "form-0-shelf": self.shelf.pk,
        }
        data.update({"form-0-" + k: v for k, v in extra.items()})
        return data

    def test_get_muestra_las_filas_temporales(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        formset = response.context["formset"]
        self.assertEqual(formset.initial, self.temp.data)

    def test_formset_invalido_se_vuelve_a_mostrar(self):
        response = self.client.post(self.url, self.fila(cantidad=1000))
        self.assertEqual(response.status_code, 200)
        self.assertIn("cantidad", response.context["formset"].errors[0])
        self.assertTrue(TemporalUploadReactive.objects.filter(pk=self.temp.pk).exists())

    def test_formset_valido_crea_reactivo_contenedor_y_objetos(self):
        response = self.client.post(self.url, self.fila())
        self.assertRedirects(
            response,
            reverse(
                "laboratory:load_archive",
                kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
            ),
            fetch_redirect_response=False,
        )
        self.assertFalse(TemporalUploadReactive.objects.filter(pk=self.temp.pk).exists())
        reactivo = Object.objects.get(name="Etanol absoluto", type=0)
        self.assertTrue(
            Object.objects.filter(name="Botella vidrio", is_container=True).exists()
        )
        so = ShelfObject.objects.get(object=reactivo, shelf=self.shelf)
        self.assertEqual(so.quantity, 10)
        self.assertIsNotNone(so.container)

    def test_clave_de_otro_laboratorio_responde_404(self):
        lab2 = Laboratory.objects.get(name="Lab Ultra")
        response = self.client.get(self.url_para(lab2, self.temp))
        assert_error_page(self, response, 404)

    def test_laboratorio_fuera_de_la_organizacion_responde_403(self):
        otra_org = OrganizationStructure.objects.get(name="Organization Testing")
        lab_ajeno = Laboratory.objects.create(name="Lab ajeno", organization=otra_org)
        response = self.client.get(self.url_para(lab_ajeno, self.temp))
        assert_error_page(self, response, 403)
