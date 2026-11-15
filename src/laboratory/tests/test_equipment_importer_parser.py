"""Lectura de los Excel de equipos (``laboratory/equipment/importer.py``), sin base de datos.

Los libros se arman en memoria con la misma forma que los del laboratorio: el
inventario con un renglón de encabezados y el PT-05 R-10 con encabezado de varias
filas y celdas combinadas.
"""
import datetime
import io

import openpyxl
from django.test import SimpleTestCase

from laboratory.equipment import importer


def as_file(workbook):
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def inventory_workbook():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inventario de trabajo asistente"
    ws.append(["Equipo", "Marca", "Modelo", "Serie", "N° Activo ", "Codigo del laboratorio",
               "Responsable", "Verificacion", "Mantenimiento interno", "Mantenimiento externo",
               "Ubicación", "Placa"])
    ws.append(["Agitador", "Corning", "PC-420D", None, None, "LB-002", "XVR", "REVISAR FUNCIONAMIENTO ",
               None, None, "Mesa de trabajo", "NI"])
    ws.append(["Autoclave", None, None, "907388", None, "LB-007", "XVR", None, None, None, None, "N00118827"])
    ws.append(["Balanza granataria", "Ballar", None, None, None, "LB-010", "Retirada EBC"])
    ws.append([None, None, None, None, None, None, None])
    return wb


def program_workbook():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Formato PT-05 R-10"
    ws["C1"] = "UNIVERSIDAD NACIONAL"
    ws["C4"] = "PT-05 R-10 PROGRAMA DE EQUIPOS"
    header = {
        "A8": "Magnitud", "B8": "Código", "C8": "Descripción", "D8": "Posición", "E8": "Estado del Equipo",
        "F8": "Datos del equipo", "F9": "Información General", "F10": "Marca", "G10": "Modelo",
        "H10": "Serie", "I10": "Versión del software y firmware", "J8": "Características metrológicas",
        "J9": "Unidad de medida", "K9": "Resolución", "L9": "Intervalo de indicaciones",
        "M8": "Responsables y uso", "M9": "Persona Responsable", "N9": "Usuarios activos",
        "O8": "Plan anual", "O9": "Calibración", "O10": "Fecha de Calibración",
        "P10": "Fecha de próxima calibración", "Q10": "Resultados", "R9": "Mantenimiento",
        "R10": "1", "R11": "Programado", "S11": "Ejecutado", "S12": "Tipo", "T12": "Inspección visual",
        "U12": "Limpieza", "V12": "Cambio de batería", "W12": "Pintura ", "X12": "Engrasado",
        "Y12": "Incluye reporte de mantenimiento", "Z12": "Afecta los resultados de la última calibración",
        "AA12": "Detalles de cualquier daño, mal funcionamiento, modificación o reparación realizada",
    }
    for cell, value in header.items():
        ws[cell] = value
    for merged in ("A8:A12", "B8:B12", "C8:C12", "D8:D12", "E8:E12", "F10:F12", "G10:G12", "H10:H12",
                   "I10:I12", "J9:J12", "K9:K12", "L9:L12", "M9:M12", "N9:N12", "O10:O12", "P10:P12",
                   "Q10:Q12", "R11:R12", "S11:AA11"):
        ws.merge_cells(merged)
    row = ["Masa", "LB-123", "Balanza Granataria", "MESA #2", "Conforme", "EMO", "DCU", "DCV-R&5212A",
           "NA", "gramos", 0.01, "0.0-5000.00", "Xindy Víquez R.", "Personal autorizado",
           datetime.datetime(2026, 4, 10), datetime.datetime(2027, 4, 10), "Conforme", 2026, "Preventivo",
           "√", "√", "x", "x", "x", "no", "no", "no"]
    for col, value in enumerate(row, start=1):
        ws.cell(13, col, value)
    ws.cell(14, 2, "LB-117")
    ws.cell(14, 3, "Micropipeta G+")
    ws.cell(14, 15, "NA")
    ws.cell(14, 17, "NA")
    return wb


class LimpiezaDeValoresTest(SimpleTestCase):

    def test_vacios_del_laboratorio(self):
        for value in (None, "", "  ", "NA", "na", "NI", "N/A", "-"):
            self.assertEqual(importer.clean(value), "", value)

    def test_marcas_de_verificacion(self):
        self.assertTrue(importer.is_checked("√"))
        self.assertTrue(importer.is_checked("Sí"))
        self.assertFalse(importer.is_checked("x"))
        self.assertFalse(importer.is_checked("no"))
        self.assertFalse(importer.is_checked(None))

    def test_fechas(self):
        self.assertEqual(importer.parse_date(datetime.datetime(2026, 4, 10)), "2026-04-10")
        self.assertEqual(importer.parse_date("10/04/2026"), "2026-04-10")
        self.assertEqual(importer.parse_date("NA"), "")
        self.assertEqual(importer.parse_date("sin fecha"), "")

    def test_numeros_enteros_sin_decimal(self):
        self.assertEqual(importer.clean(31456.0), "31456")
        self.assertEqual(importer.clean(0.01), "0.01")


class InventarioTest(SimpleTestCase):

    def test_lee_por_encabezado_y_detecta_bajas(self):
        title, rows = importer.read_workbook(as_file(inventory_workbook()), importer.INVENTORY)
        self.assertEqual(title, "Inventario de trabajo asistente")
        self.assertEqual([row["internal_code"] for row in rows], ["LB-002", "LB-007", "LB-010"])
        agitador, autoclave, balanza = rows
        self.assertEqual(agitador["brand"], "Corning")
        self.assertEqual(agitador["notes"], "REVISAR FUNCIONAMIENTO")
        self.assertEqual(agitador["asset_number"], "")  # Placa «NI»
        self.assertEqual(autoclave["asset_number"], "N00118827")  # la placa a falta de activo
        self.assertTrue(balanza["decommissioned"])
        self.assertEqual(balanza["responsible"], "EBC")
        self.assertFalse(agitador["decommissioned"])

    def test_columnas_en_otro_orden(self):
        wb = openpyxl.Workbook()
        wb.active.append(["Ubicación", "Codigo del laboratorio", "Equipo"])
        wb.active.append(["Sala Maldi", "LB-200", "Centrífuga"])
        _title, rows = importer.read_workbook(as_file(wb), importer.INVENTORY)
        self.assertEqual(rows[0]["physical_location"], "Sala Maldi")
        self.assertEqual(rows[0]["name"], "Centrífuga")

    def test_hoja_sin_formato(self):
        wb = openpyxl.Workbook()
        wb.active.append(["Cualquier", "cosa"])
        self.assertEqual(importer.read_workbook(as_file(wb), importer.INVENTORY), (None, []))


class ProgramaTest(SimpleTestCase):

    def test_encabezado_combinado_y_bloque_de_mantenimiento(self):
        title, rows = importer.read_workbook(as_file(program_workbook()), importer.PROGRAM)
        self.assertEqual(title, "Formato PT-05 R-10")
        self.assertEqual(len(rows), 2)
        balanza = rows[0]
        self.assertEqual(balanza["internal_code"], "LB-123")
        self.assertEqual(balanza["magnitude"], "Masa")
        self.assertEqual(balanza["brand"], "EMO")
        self.assertEqual(balanza["serial_number"], "DCV-R&5212A")
        self.assertEqual(balanza["software_version"], "")
        self.assertEqual(balanza["measurement_unit"], "gramos")
        self.assertEqual(balanza["resolution"], "0.01")
        self.assertEqual(balanza["responsible"], "Xindy Víquez R.")
        self.assertEqual(balanza["calibration_date"], "2026-04-10")
        self.assertEqual(balanza["next_calibration_date"], "2027-04-10")
        self.assertEqual(balanza["calibration_conformity"], "conforming")
        self.assertEqual(balanza["maintenance"], [{
            "programmed_year": 2026, "type": "preventive", "executed": True,
            "activities": ["Inspección visual", "Limpieza"], "includes_report": False,
            "affects_calibration": False, "damage_details": "",
        }])

    def test_equipo_sin_calibracion(self):
        _title, rows = importer.read_workbook(as_file(program_workbook()), importer.PROGRAM)
        micropipeta = rows[1]
        self.assertEqual(micropipeta["calibration_date"], "")
        self.assertEqual(micropipeta["calibration_conformity"], "")
        self.assertEqual(micropipeta["maintenance"], [])

    def test_detecta_las_hojas_de_un_libro(self):
        wb = program_workbook()
        inventario = wb.create_sheet("Inventario")
        for row in inventory_workbook().active.iter_rows(values_only=True):
            inventario.append(row)
        found = importer.detect_sheets(wb)
        self.assertEqual(
            [(title, kind) for title, kind, _count in found],
            [("Formato PT-05 R-10", importer.PROGRAM), ("Inventario", importer.INVENTORY)],
        )
