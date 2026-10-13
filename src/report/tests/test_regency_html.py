"""El reporte de regencia en HTML guarda su tabla (antes salía siempre vacío)."""

from unittest.mock import patch

from report.tests.utils import ReportTestBase
from report.views.regency import (
    get_pdf_regency_table_content,
    report_regency_html,
)

RESULTADO = {
    "clasificacion": "riesgo menor",
    "criterio": "Sumatoria por debajo de 1.",
    "sumatorias_por_categoria": {"Físico": 0.2, "Salud": 0.1},
    "detalles": [
        {
            "nombre": "Acetona",
            "cas": "67-64-1",
            "cantidad_t": 0.5,
            "nominada_c3": False,
            "umbral_c3": None,
            "ratio_c3": None,
            "h_codes": "H225",
            "regla_cruzada_salud": False,
            "detalle_contribuciones": "",
            "advertencias": "",
            "contribuciones": {"Físico": 0.2},
        }
    ],
    "trazabilidad": {},
}


class RegencyHtmlTest(ReportTestBase):

    def report(self):
        return self.make_report("regency_report", "html", years=2025, period="")

    def test_html_guarda_columnas_filas_y_resumen(self):
        report = self.report()
        with patch("report.views.regency.clasificar_establecimiento", return_value=RESULTADO):
            total = report_regency_html(report)
        report.refresh_from_db()
        self.assertEqual(total, 1)
        self.assertEqual(len(report.table_content["dataset"]), 1)
        self.assertEqual(report.table_content["dataset"][0][0], "Acetona")
        self.assertEqual(report.table_content["summary"]["classification"], "riesgo menor")
        self.assertEqual(report.table_content["summary"]["environmental"], 0.0)

    def test_el_pdf_reutiliza_lo_calculado(self):
        report = self.report()
        with patch(
            "report.views.regency.clasificar_establecimiento", return_value=RESULTADO
        ) as clasificar:
            report_regency_html(report)
            html = get_pdf_regency_table_content(report)
        self.assertEqual(clasificar.call_count, 1)
        self.assertIn("Acetona", html)
        self.assertIn("riesgo menor", html)
