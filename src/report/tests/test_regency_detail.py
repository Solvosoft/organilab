from datetime import date, datetime
from unittest.mock import patch

import openpyxl
import pyexcel
from django.utils import timezone

from laboratory.models import Object, ObjectMaximumLimit
from report.tests.utils import ReportTestBase
from laboratory.report_utils import BRAND, RISK_COLORS
from report.views.regency import report_regency
from risk_management.tests.test_clasificacion_regencia import cuadro3, cuadro4, inventario as inventario_c3
from risk_management.utils_risk import clasificar_establecimiento, get_inventory

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
FORMATOS = ("xlsx", "xls", "ods")


class RegencyReportDetailTest(ReportTestBase):
    """El informe regencial: mismas hojas y filas en XLSX, XLS y ODS."""

    def report(self, file_type, **data):
        data.setdefault("period", "01/01/2024 - 31/12/2024")
        return self.make_report("regency_report", file_type, **data)

    def classify(self, **kwargs):
        return patch("report.views.regency.clasificar_establecimiento", **kwargs)

    def generate(self, file_type, resultado=RESULTADO, **data):
        report = self.report(file_type, **data)
        with self.classify(return_value=resultado):
            total = report_regency(report)
        report.refresh_from_db()
        return report, total

    def sheets(self, report):
        """{hoja: filas} sin las celdas vacías del final, igual para los tres formatos."""
        with report.file.open("rb") as fh:
            book = pyexcel.get_book(file_type=report.file_type, file_content=fh.read())
        result = {}
        for sheet in book:
            rows = []
            for row in sheet.to_array():
                row = ["" if cell is None else cell for cell in row]
                while row and row[-1] == "":
                    row.pop()
                rows.append(row)
            result[sheet.name] = rows
        return result

    def test_los_tres_formatos_tienen_el_mismo_contenido(self):
        contenidos = {}
        for file_type in FORMATOS:
            report, total = self.generate(file_type)
            self.assertEqual(total, 2)
            contenidos[file_type] = self.sheets(report)
        self.assertEqual(list(contenidos["xlsx"]), ["Resumen", "Sumatoria_categoría", "Detalle"])
        self.assertEqual(contenidos["xls"], contenidos["xlsx"])
        self.assertEqual(contenidos["ods"], contenidos["xlsx"])

    def test_resumen_con_titulo_periodo_y_clasificacion(self):
        report, _total = self.generate("xlsx")
        resumen = self.sheets(report)["Resumen"]
        self.assertEqual(resumen[0], ["Reporte de prueba"])
        self.assertEqual(resumen[1][1], "01/01/2024 - 31/12/2024")
        self.assertEqual(resumen[4], ["riesgo menor", "Sumatorias por debajo de 1."])

    def test_sin_periodo_y_sin_registros_no_hay_rango(self):
        report, _total = self.generate("xlsx", period="")
        self.assertEqual(self.sheets(report)["Resumen"][1][1], "-")

    def test_sin_periodo_va_del_primer_registro_a_hoy(self):
        reactivo = Object.objects.filter(type=Object.REACTIVE).first()
        for created_at in (date(2023, 5, 4), date(2025, 1, 2)):
            limite = ObjectMaximumLimit.objects.create(
                laboratory=self.lab, object=reactivo, measurement_unit=self.unit()
            )
            ObjectMaximumLimit.objects.filter(pk=limite.pk).update(created_at=created_at)
        report, _total = self.generate("xlsx", period="")
        hoy = timezone.localdate().strftime("%d/%m/%Y")
        self.assertEqual(self.sheets(report)["Resumen"][1][1], "04/05/2023 - " + hoy)

    def test_detalle_y_filtro_del_periodo(self):
        report = self.report("xlsx")
        with self.classify(return_value=RESULTADO), patch(
            "report.views.regency.get_inventory", wraps=get_inventory
        ) as inventario:
            report_regency(report)
        filtros = inventario.call_args.args[0]
        self.assertEqual(
            filtros["created_at__range"], [datetime(2024, 1, 1), datetime(2024, 12, 31)]
        )
        self.assertEqual(filtros["laboratory__pk__in"], [self.lab.pk])
        report.refresh_from_db()
        detalle = self.sheets(report)["Detalle"]
        self.assertEqual(detalle[1][:4], ["Cal", "1305-78-8", 1.235, "Yes"])
        self.assertEqual(detalle[1][8], "Salud: 1/2 | Físico: 1/4")
        self.assertEqual(detalle[1][9], "sin condición")
        self.assertEqual(detalle[1][10:], [0.5, 0.25, 0.0])
        self.assertEqual(detalle[2][8:10], ["", ""])

    def test_si_el_calculo_falla_queda_sin_datos(self):
        for file_type in FORMATOS:
            with self.subTest(formato=file_type):
                report = self.report(file_type, period="")
                with self.classify(side_effect=ValueError("tabla incompleta")):
                    self.assertEqual(report_regency(report), 0)
                report.refresh_from_db()
                hojas = self.sheets(report)
                self.assertEqual(hojas["Resumen"][4][0], "riesgo menor")
                self.assertEqual(hojas["Detalle"], [["Data not available"]])

    def test_riesgo_mayor_por_cuadro3_no_cae_en_el_respaldo(self):
        resultado = clasificar_establecimiento(
            inventario_c3(("Cloro", "7782-50-5", 15.0, "H270", "")),
            cuadro3({"cas": "7782-50-5", "umbral_t": 10.0}),
            cuadro4(),
            {},
        )
        for file_type in FORMATOS:
            with self.subTest(formato=file_type):
                report, _total = self.generate(file_type, resultado=resultado, period="")
                hojas = self.sheets(report)
                self.assertEqual(hojas["Resumen"][4][0], "riesgo mayor")
                self.assertEqual(hojas["Detalle"][1][0], "Cloro")
                self.assertNotIn("riesgo menor", [c for fila in hojas["Detalle"] for c in fila])

    def test_periodo_con_fecha_invalida_no_filtra_por_fecha(self):
        report = self.report("xlsx", period="ayer - hoy")
        with self.classify(return_value=RESULTADO), patch(
            "report.views.regency.get_inventory", wraps=get_inventory
        ) as inventario:
            report_regency(report)
        self.assertNotIn("created_at__range", inventario.call_args.args[0])

    def test_estilos_del_xlsx(self):
        report, _total = self.generate("xlsx")
        with report.file.open("rb") as fh:
            wb = openpyxl.load_workbook(fh)
        resumen = wb["Resumen"]
        self.assertTrue(resumen["A1"].font.b)
        self.assertTrue(resumen["A2"].font.b)
        self.assertEqual(resumen["A4"].fill.fgColor.rgb[-6:], BRAND)
        self.assertEqual(resumen["A5"].fill.fgColor.rgb[-6:], RISK_COLORS["risk_low"][0])
        detalle = wb["Detalle"]
        self.assertEqual(detalle.freeze_panes, "A2")
        self.assertIsNotNone(detalle.auto_filter.ref)
        self.assertTrue(detalle["A2"].alignment.wrap_text)
