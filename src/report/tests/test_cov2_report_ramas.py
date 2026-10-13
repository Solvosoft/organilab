"""Ramas de la app `report` que ninguna otra prueba recorría.

Cada clase cubre un caso límite concreto de un reporte o de su API: la lista
de muebles vacía, la fila repetida por un filtro a muchos, la unidad sin base,
la organización que no existe... Son caminos reales, alcanzables desde la
interfaz o desde la tarea Celery, que solo se ejercitaban (o ni eso) en
Selenium.
"""

from unittest.mock import patch

from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from auth_and_perms.models import Profile
from laboratory.models import (
    Catalog,
    Object,
    PrecursorReport,
    PrecursorReportValues,
    Shelf,
    ShelfObject,
)
from report.datasets import shelfobjects_by_furniture
from report.forms import ValidateObjectTypeForm
from report.tests.utils import XHR, ReportTestBase
from report.views import discard_objects, riskzones, stock
from report.views.base import base_pdf
from report.views.object_changes import _unlogged_with_history
from report.views.regency import get_pdf_regency_table_content
from sga.models import DangerIndication, SubstanceCharacteristics

# Resultado fijo de la clasificación de regencia (no se importa de
# test_regency_html para no volver a correr sus pruebas desde este módulo).
RESULTADO = {
    "clasificacion": "riesgo menor",
    "criterio": "Sumatoria por debajo de 1.",
    "sumatorias_por_categoria": {"Físico": 0.2},
    "detalles": [
        {
            "nombre": "Acetona", "cas": "67-64-1", "cantidad_t": 0.5,
            "nominada_c3": False, "umbral_c3": None, "ratio_c3": None,
            "h_codes": "H225", "regla_cruzada_salud": False,
            "detalle_contribuciones": "", "advertencias": "",
            "contribuciones": {"Físico": 0.2},
        }
    ],
    "trazabilidad": {},
}


class ShelfobjectsByFurnitureTest(ReportTestBase):
    """`shelfobjects_by_furniture`, el recorrido común de los reportes por mueble."""

    def test_sin_muebles_no_consulta(self):
        with self.assertNumQueries(0):
            self.assertEqual(list(shelfobjects_by_furniture([])), [])

    def test_filtro_a_muchos_no_repite_filas(self):
        """Un filtro por códigos H cruza una relación a muchos: el JOIN repite
        la unidad una vez por código, y el reporte la listaría dos veces."""
        codes = list(DangerIndication.objects.order_by("code")[:2])
        obj = Object.objects.create(
            code="COV2-H", name="Con dos códigos", type=Object.REACTIVE, organization=self.org
        )
        SubstanceCharacteristics.objects.create(object_related=obj).h_code.set(codes)
        shelfobject = self.make_shelfobject(obj)
        furniture = Shelf.objects.get(pk=1).furniture

        filas = list(
            shelfobjects_by_furniture(
                [furniture],
                filters={"object__substancharacteristics_object__h_code__in": codes},
            )
        )
        self.assertEqual(filas, [(furniture, shelfobject)])


class PrecursorValuesPkCeroTest(ReportTestBase):
    """La API de valores de precursores con un pk de reporte que no existe.

    `<int:precusor_pk>` acepta 0 y el viewset lo trataba como «falta el pk»:
    lanzaba el `ValidationError` de Django, que DRF no traduce, y respondía 500.
    Ahora el pk se busca como cualquier otro y responde 404.
    """

    def setUp(self):
        super().setUp()
        content_type = ContentType.objects.get_for_model(PrecursorReportValues)
        self.user.user_permissions.add(
            Permission.objects.get(content_type=content_type, codename="view_precursorreportvalues")
        )

    def test_reporte_cero_es_404(self):
        url = reverse(
            "report:api-precursor-report-values-list",
            kwargs={"org_pk": self.org.pk, "precusor_pk": 0},
        )
        self.assertEqual(self.client.get(url, **XHR).status_code, 404)

    def test_reporte_existente_responde(self):
        precursor = PrecursorReport.objects.create(
            month=3, month_belong=2, year=2024, laboratory=self.lab
        )
        url = reverse(
            "report:api-precursor-report-values-list",
            kwargs={"org_pk": self.org.pk, "precusor_pk": precursor.pk},
        )
        self.assertEqual(self.client.get(url, **XHR).status_code, 200)


class DownloadOrganizationReportSuperuserTest(ReportTestBase):
    """Un superusuario salta `ProfileMiddleware`, así que la organización
    inexistente llega hasta la vista y es ella la que responde 401."""

    def test_organizacion_inexistente_es_401(self):
        root = User.objects.create_superuser("cov2-root", "root@example.com", "x")
        # Sin perfil, ProfileLanguageMiddleware corta antes con un 404.
        Profile.objects.create(user=root)
        self.client.force_login(root)
        response = self.client.get(
            reverse("report:generate_organization_report", kwargs={"org_pk": 999999}),
            {"task": "x", "taskreport": 1},
            **XHR,
        )
        self.assertEqual(response.status_code, 401)


class RegencyPdfTest(ReportTestBase):
    """El PDF de regencia, pedido sin haber generado antes el HTML."""

    def report(self, file_type):
        return self.make_report("regency_report", file_type, years=2025, period="")

    def test_tabla_pdf_calcula_si_no_hay_resumen(self):
        report = self.report("pdf")
        with patch(
            "report.views.regency.clasificar_establecimiento", return_value=RESULTADO
        ) as clasificar:
            html = get_pdf_regency_table_content(report)
        self.assertEqual(clasificar.call_count, 1)
        self.assertIn("Acetona", html)

    def test_base_pdf_usa_la_tabla_de_regencia(self):
        report = self.report("pdf")
        with patch("report.views.regency.clasificar_establecimiento", return_value=RESULTADO):
            base_pdf(report, "http://testserver/")
        report.refresh_from_db()
        self.assertTrue(report.file.name.endswith(".pdf"))
        self.assertIn("summary", report.table_content)


class DiscardColumnListTest(ReportTestBase):
    def test_columnas_elegidas(self):
        desecho = Shelf.objects.get(pk=5)
        cal = Object.objects.get(pk=2)
        self.make_shelfobject(cal, shelf=desecho, quantity=3)
        report = self.make_report("report_waste_objects", "html")
        filas = discard_objects.get_dataset_report_discard_objects(
            report, self.lab, ["object", "amount"]
        )
        self.assertIn([cal.name, "3.0"], filas)


class UnloggedWithHistoryTest(ReportTestBase):
    def test_todo_el_inventario_tiene_movimientos(self):
        """Si cada unidad del inventario ya tiene movimientos en el periodo, no
        queda nada que listar en cero ni historia que buscar."""
        shelfobject = ShelfObject.objects.get(pk=2)
        groups = {
            (shelfobject.in_where_laboratory_id, shelfobject.object_id, shelfobject.measurement_unit_id): []
        }
        with self.assertNumQueries(1):
            resultado = _unlogged_with_history(groups, ShelfObject.objects.filter(pk=shelfobject.pk))
        self.assertEqual(resultado, ({}, set()))


class StockCartelSkipsTest(ReportTestBase):
    """El cartel de inventario omite lo que no puede agrupar."""

    def test_unidad_sin_base_y_estado_desconocido(self):
        obj = Object.objects.create(
            code="COV2-C", name="Reactivo cartel", type=Object.REACTIVE, organization=self.org
        )
        sin_base = Catalog.objects.create(key="units", description="Unidad sin base")
        self.make_shelfobject(obj, measurement_unit=sin_base)
        self.make_shelfobject(obj, physical_status="plasma")
        report = self.make_report("chemicalinventory", "html")
        filas = stock.get_stock_cartel_dataset(report)
        self.assertNotIn(obj.name, [f[1] for f in filas])

        # Con un estado válido la misma sustancia sí aparece.
        self.make_shelfobject(obj, physical_status="solid")
        self.assertIn(obj.name, [f[1] for f in stock.get_stock_cartel_dataset(report)])


class RiskZoneBoxTest(ReportTestBase):
    def test_caja_multiplica_unidades_por_cajas(self):
        """2 cajas de 1000 ml son 2 L: superan un umbral de 1.5 que 2 ml no superarían."""
        obj = Object.objects.create(
            code="COV2-R", name="Reactivo en cajas", type=Object.REACTIVE, organization=self.org,
            is_dangerous=True, has_threshold=True, threshold=0.0015,
        )
        self.make_shelfobject(
            obj, quantity=2, is_box=True, quantity_units=[{"units": 1000, "quantity": 1}]
        )
        report = self.make_report("risk_zone_report", "html", risk_zone=[], building=[])
        columnas = ["name", "threshold"]
        filas = riskzones.get_dataset_report(report, columnas)
        self.assertIn([obj.name, "Yes Exceeds Threshold"], filas)


class ValidateObjectTypeFormTest(ReportTestBase):
    def test_vacio_es_obligatorio_y_tipo_desconocido_se_rechaza(self):
        vacio = ValidateObjectTypeForm({"type_id": ""})
        self.assertFalse(vacio.is_valid())
        self.assertIn("type_id", vacio.errors)

        raro = ValidateObjectTypeForm({"type_id": "9"})
        self.assertFalse(raro.is_valid())

        valido = ValidateObjectTypeForm({"type_id": Object.REACTIVE})
        self.assertTrue(valido.is_valid())
        self.assertEqual(valido.cleaned_data["type_id"], Object.REACTIVE)
