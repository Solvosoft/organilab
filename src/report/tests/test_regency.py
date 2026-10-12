from unittest.mock import patch

import openpyxl
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from laboratory.models import Catalog, Laboratory
from report.models import TaskReport
from report.views.regency import report_regency_doc, report_regency_xlsx


@override_settings(MEDIA_ROOT="/tmp/organilab-test-media")
class RegencyReportWithoutTonsUnitTest(TestCase):
    """El reporte de regencia se genera aunque falte la unidad «Toneladas».

    La unidad la crea una migración de datos, así que no está en una base
    vaciada y cargada desde fixtures (la de Selenium) ni tiene por qué sobrevivir
    a una depuración del catálogo. `get_inventory` la pedía con `.get()` y la
    tarea del reporte moría con DoesNotExist; el usuario se quedaba esperando un
    estado que nunca llegaba. Tampoco hay límites máximos registrados: el
    inventario sale vacío y eso no debe romper el `drop_duplicates` posterior.
    """

    fixtures = ["laboratory_data.json"]

    def setUp(self):
        Catalog.objects.filter(key="units", description="Toneladas").delete()

    def build_report(self, file_type):
        lab = Laboratory.objects.first()
        return TaskReport.objects.create(
            created_by=User.objects.first(),
            type_report="regency_report",
            file_type=file_type,
            data={
                "name": "rep-regencia",
                "title": "Reporte de regencia",
                "organization": lab.organization_id,
                "laboratory": [lab.pk],
                "period": "",
            },
            language="es",
        )

    def test_xlsx_se_genera(self):
        report = self.build_report("xlsx")
        report_regency_xlsx(report)
        report.refresh_from_db()
        self.assertTrue(report.file)

    def test_ods_se_genera(self):
        report = self.build_report("ods")
        report_regency_doc(report)
        report.refresh_from_db()
        self.assertTrue(report.file)

    def test_riesgo_mayor_sin_sumatorias_no_se_publica_como_menor(self):
        """«Riesgo mayor» por Cuadro 3/4 llega sin sumatorias por categoría.

        Leerlas con `[]` tiraba KeyError y el `except` del reporte escribía
        «riesgo menor»: invertía una clasificación regulatoria.
        """
        resultado = {
            "clasificacion": "riesgo mayor",
            "criterio": "Sustancia nominada sobre su umbral.",
            "sumatorias_por_categoria": {},
            "detalles": [],
            "trazabilidad": {},
        }
        report = self.build_report("xlsx")
        with patch(
            "report.views.regency.clasificar_establecimiento", return_value=resultado
        ):
            report_regency_xlsx(report)
        report.refresh_from_db()
        with report.file.open("rb") as fh:
            wb = openpyxl.load_workbook(fh)
        self.assertEqual(wb["Resumen"]["A2"].value, "riesgo mayor")
        self.assertEqual(
            [c.value for c in wb["Sumatoria_categoría"][2]], [0.0, 0.0, 0.0]
        )
