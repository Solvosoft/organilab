from datetime import datetime
from unittest.mock import patch

import openpyxl
import pyexcel

from report.tests.utils import ReportTestBase
from report.views.regency import report_regency_doc, report_regency_xlsx
from risk_management.utils_risk import get_inventory

DETALLE = {
    "nombre": "Cal",
    "cas": "1305-78-8",
    "cantidad_t": 1.23456,
    "nominada_c3": True,
    "umbral_c3": 10,
    "ratio_c3": 0.1,
    "h_codes": "H314",
    "regla_cruzada_salud": False,
    "detalle_contribuciones": ["Salud: 1/2", "Físico: 1/4"],
    "advertencias": ["sin condición"],
    "contribuciones": {"Salud": 0.5, "Físico": 0.25},
}
RESULTADO = {
    "clasificacion": "riesgo menor",
    "criterio": "Sumatorias por debajo de 1.",
    "sumatorias_por_categoria": {"Físico": 0.25, "Salud": 0.5, "Ambiental": 0.0},
    "detalles": [DETALLE, dict(DETALLE, detalle_contribuciones=[], advertencias=[], nombre="Sal")],
    "trazabilidad": {},
}


class RegencyReportDetailTest(ReportTestBase):
    """Hojas de detalle del reporte de regencia y su respaldo si el cálculo falla."""

    def report(self, file_type, **data):
        data.setdefault("period", "01/01/2024 - 31/12/2024")
        return self.make_report("regency_report", file_type, **data)

    def classify(self, **kwargs):
        return patch("report.views.regency.clasificar_establecimiento", **kwargs)

    def test_xlsx_con_detalle_y_periodo(self):
        report = self.report("xlsx")
        with self.classify(return_value=RESULTADO), patch(
            "report.views.regency.get_inventory", wraps=get_inventory
        ) as inventario:
            report_regency_xlsx(report)
        filtros = inventario.call_args.args[0]
        self.assertEqual(
            filtros["created_at__range"], [datetime(2024, 1, 1), datetime(2024, 12, 31)]
        )
        self.assertEqual(filtros["laboratory__pk__in"], [self.lab.pk])
        report.refresh_from_db()
        with report.file.open("rb") as fh:
            wb = openpyxl.load_workbook(fh)
        detalle = [list(r) for r in wb["Detalle"].iter_rows(values_only=True)]
        self.assertEqual(detalle[1][:4], ["Cal", "1305-78-8", 1.235, "Yes"])
        self.assertEqual(detalle[1][8], "Salud: 1/2 | Físico: 1/4")
        self.assertEqual(detalle[1][9], "sin condición")
        self.assertEqual(detalle[1][10:], [0.5, 0.25, 0.0])
        self.assertEqual(detalle[2][8:10], [None, None])

    def test_xlsx_si_el_calculo_falla_queda_sin_datos(self):
        report = self.report("xlsx", period="")
        with self.classify(side_effect=ValueError("tabla incompleta")):
            report_regency_xlsx(report)
        report.refresh_from_db()
        with report.file.open("rb") as fh:
            wb = openpyxl.load_workbook(fh)
        self.assertEqual(wb["Resumen"]["A2"].value, "riesgo menor")
        self.assertEqual(wb["Detalle"]["A1"].value, "Data not available")

    def test_ods_con_detalle(self):
        report = self.report("ods")
        with self.classify(return_value=RESULTADO), patch(
            "report.views.regency.get_inventory", wraps=get_inventory
        ) as inventario:
            filas = report_regency_doc(report)
        self.assertIn("created_at__range", inventario.call_args.args[0])
        self.assertEqual(filas, 12)
        report.refresh_from_db()
        with report.file.open("rb") as fh:
            hoja = pyexcel.get_array(file_type="ods", file_content=fh.read())
        self.assertEqual(hoja[0][0], "reporte-prueba")
        self.assertEqual(hoja[2][0], "riesgo menor")
        cal = [f for f in hoja if f and f[0] == "Cal"][0]
        self.assertEqual(cal[3], "Yes")
        self.assertEqual(cal[7], "No")

    def test_ods_si_el_calculo_falla(self):
        report = self.report("ods", laboratory=[])
        with self.classify(side_effect=KeyError("Salud")):
            report_regency_doc(report)
        report.refresh_from_db()
        with report.file.open("rb") as fh:
            hoja = pyexcel.get_array(file_type="ods", file_content=fh.read())
        self.assertEqual(hoja[2][0], "riesgo menor")
        self.assertEqual(hoja[-1][0], "Data not available")
