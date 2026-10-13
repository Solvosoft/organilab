# encoding: utf-8
"""Ramas de las vistas, etiquetas y utilidades de ``laboratory`` que la suite no tocaba.

Se cubren por el camino real: rutas con el cliente de pruebas y etiquetas o
utilidades llamadas como lo hacen las plantillas.  Incluye lo nuevo de la rama de
rendimiento: el QR de salas, muebles y estantes servido por URL (``qr_nodes``) y
el mapa de unidades compartido (``utils_base_unit.cached_units``).
"""

from django.urls import reverse

from laboratory import qr_nodes
from laboratory import utils_base_unit
from laboratory.forms import ObjectMaterialForm
from laboratory.models import Furniture, Laboratory, LaboratoryRoom, Shelf
from laboratory.templatetags import lab_data_retriever
from laboratory.templatetags import laboratory as labtags
from laboratory.tests.test_cov_views_shelfobject import BaseShelfObjectLegacyTest
from laboratory.tests.utils import BaseLaboratorySetUpTest

AJAX = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


class VistasHeredadasConLaboratorioAjenoTest(BaseShelfObjectLegacyTest):
    """Las vistas legacy de shelfobject piden que el laboratorio de la URL sea de
    la organización de la URL.  Con el laboratorio de otra organización la
    comprobación de acceso corta antes de buscar el objeto."""

    def url_ajena(self, name, **kwargs):
        kwargs.update({"org_pk": self.org.pk, "lab_pk": self.lab_ajeno.pk})
        return reverse("laboratory:" + name, kwargs=kwargs)

    def test_listado_de_objetos_con_laboratorio_ajeno_da_404(self):
        data = self.client.get(
            self.url_ajena("list_shelfobject"), {"shelf": self.shelf_ajeno.pk}, **AJAX
        ).json()
        self.assertEqual(data["status"], 404)

    def test_limite_con_laboratorio_ajeno_da_404(self):
        url = self.url_ajena("get_shelfobject_limit", pk=self.so_ajeno.pk)
        self.assertNegado(self.client.post(url, {"amount": "99"}, **AJAX), 404)
        self.so_ajeno.refresh_from_db()
        self.assertEqual(self.so_ajeno.limit_quantity, 1)

    def test_detalle_de_equipo_con_laboratorio_ajeno_da_404(self):
        url = self.url_ajena("equipment_shelfobject_detail", pk=self.so_ajeno.pk)
        self.assertNegado(self.client.get(url, **AJAX), 404)


class SalasYCatalogosTest(BaseLaboratorySetUpTest):

    def test_edicion_de_sala_ofrece_el_formulario_de_mueble(self):
        """Defecto corregido: un segundo ``get_context_data`` tapaba al que añadía
        ``furniture_form`` y el modal «Crear mueble» de la edición salía vacío."""
        url = reverse(
            "laboratory:rooms_update",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": self.labroom.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("furniture_form", response.context)
        self.assertEqual(response.context["object"], self.labroom)

    def test_alta_de_tipo_de_estructura_usa_su_propia_ruta(self):
        url = reverse("laboratory:add_structure_type_catalog")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        # Sin la rama propia el formulario se enviaba a la ruta de tipos de mueble.
        self.assertIn('action="%s"' % url, data["message"])


class MaterialContenedorTest(BaseLaboratorySetUpTest):

    def test_contenedor_sin_capacidad_la_exige(self):
        form = ObjectMaterialForm(
            data={"is_container": True, "capacity_measurement_unit": 64}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("capacity", form.errors)

    def test_capacidad_negativa_la_rechaza_el_campo(self):
        """El ``elif capacity < 0`` que había en ``clean`` era inalcanzable: el
        ``min_value`` del campo rechaza el valor antes y no llega a cleaned_data."""
        form = ObjectMaterialForm(
            data={"is_container": True, "capacity": -2, "capacity_measurement_unit": 64}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("capacity", form.errors)
        self.assertNotIn("capacity", form.cleaned_data)


class QRDeNodosTest(BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        self.room = LaboratoryRoom.objects.filter(laboratory=self.lab).first()
        self.furniture = Furniture.objects.filter(labroom=self.room).first()
        self.shelf = Shelf.objects.filter(furniture=self.furniture).first()

    def test_laboratorio_de_cada_tipo_de_nodo(self):
        for nodo in (self.room, self.furniture, self.shelf):
            with self.subTest(nodo=type(nodo).__name__):
                self.assertEqual(qr_nodes.node_laboratory_pk(nodo), self.lab.pk)

    def test_tipo_sin_qr_no_tiene_url(self):
        # Solo salas, muebles y estantes tienen QR por URL.
        self.assertIsNone(qr_nodes.node_qr_url(self.org.pk, self.lab.pk, self.lab))
        self.assertTrue(
            qr_nodes.node_qr_url(self.org.pk, self.lab.pk, self.shelf).endswith(
                "/shelf/%d.svg" % self.shelf.pk
            )
        )

    def test_etiqueta_sin_laboratorio_en_el_contexto_lo_deduce_del_nodo(self):
        html = labtags.get_qr_svg_img({}, self.shelf, organization=self.org.pk)
        esperado = qr_nodes.node_qr_url(self.org.pk, self.lab.pk, self.shelf)
        self.assertIn(esperado, html)

    def test_etiqueta_con_un_objeto_sin_qr_no_pinta_nada(self):
        html = labtags.get_qr_svg_img(
            {"laboratory": self.lab.pk}, self.lab, organization=self.org.pk
        )
        self.assertEqual(html, "")


class ConteosDeLaboratorioTest(BaseLaboratorySetUpTest):

    def test_sin_anotacion_se_cuenta_con_una_consulta(self):
        """La tarjeta de laboratorio lee los conteos ya anotados; si el
        laboratorio llega sin anotar, los filtros cuentan por su cuenta y dan lo
        mismo."""
        anotado = lab_data_retriever.annotate_object_counts(
            Laboratory.objects.filter(pk=self.lab.pk)
        ).get()
        sin_anotar = Laboratory.objects.get(pk=self.lab.pk)
        for filtro in ("get_materiales_lab", "get_equipo_lab", "get_reactivos_lab"):
            with self.subTest(filtro=filtro):
                funcion = getattr(lab_data_retriever, filtro)
                self.assertEqual(funcion(sin_anotar), funcion(anotado))


class MapaDeUnidadesTest(BaseLaboratorySetUpTest):

    def test_bloques_anidados_comparten_el_mapa(self):
        """Un reporte que llama a otro dentro de ``cached_units`` no recarga el
        catálogo: el bloque interior reutiliza el mapa del exterior."""
        with utils_base_unit.cached_units() as exterior:
            with self.assertNumQueries(0):
                with utils_base_unit.cached_units() as interior:
                    self.assertIs(interior, exterior)
                    utils_base_unit.get_unit_info(63)
        # Al salir del bloque exterior el mapa se descarta.
        self.assertIsNone(utils_base_unit._unit_map.get())

    def test_unidad_nula_no_tiene_informacion(self):
        with self.assertNumQueries(0):
            self.assertIsNone(utils_base_unit.get_unit_info(None))
