from datetime import date, datetime, timezone as dt_timezone

import xlrd
from django.utils import translation

from laboratory.models import MaterialCapacity, Object, Shelf, ShelfObject
from report.forms import ReactiveStockReportForm
from report.tests.utils import ReportTestBase
from report.views import discard_objects, stock
from sga.models import SubstanceCharacteristics


def as_rows(report):
    names = [c["name"] for c in report.table_content["columns"]]
    return [dict(zip(names, row)) for row in report.table_content["dataset"]]


class StockReportTest(ReportTestBase):
    """Inventario de sustancias: reactivos sueltos y reactivos dentro de envases."""

    def setUp(self):
        super().setUp()
        self.cal = Object.objects.get(pk=2)
        self.cal.is_pure = True
        self.cal.threshold = 3
        self.cal.save()
        SubstanceCharacteristics.objects.filter(object_related=self.cal).update(
            molecular_formula="CaO", cas_id_number="1305-78-8"
        )
        # El fixture guarda «Tanque» (reactivo) dentro de la unidad 6 (material).
        self.envase = ShelfObject.objects.get(pk=6)
        MaterialCapacity.objects.create(
            object=self.envase.object, capacity=250,
            capacity_measurement_unit=self.unit(),
        )
        ShelfObject.objects.filter(pk=14).update(
            physical_status="liquid", reactive_expiration_date=date(2030, 5, 1)
        )
        # La primera unidad suelta de «Cal» (pk 2) es la que da estado y vencimiento.
        ShelfObject.objects.filter(pk=2).update(
            physical_status="solid", reactive_expiration_date=date(2031, 1, 2)
        )
        # Un reactivo en otro envase, sin estado ni vencimiento.
        self.make_shelfobject(self.cal, quantity=2, container=ShelfObject.objects.get(pk=9))
        self.make_shelfobject(
            self.cal, quantity=1, is_box=True,
            quantity_units=[{"units": 2, "quantity": 5}],
        )

    def test_dataset_por_laboratorio(self):
        filas = stock.get_stock_dataset(self.lab.pk)
        por_nombre = {}
        for fila in filas:
            por_nombre.setdefault(fila[0], []).append(fila)

        tanque = [f for f in por_nombre["Tanque 1000 mL"] if f[9]][0]
        self.assertEqual(tanque[3], "Liquid")
        self.assertEqual(tanque[5], "Litros")
        self.assertEqual(tanque[6], 250)
        self.assertEqual(tanque[7], self.unit().description)
        self.assertEqual(tanque[8], 1)
        self.assertEqual(tanque[9], self.envase.object.name)
        self.assertEqual(tanque[12], "01/05/2030")

        en_envase = [f for f in por_nombre[self.cal.name] if f[9]][0]
        self.assertEqual((en_envase[3], en_envase[12]), ("", ""))
        self.assertEqual(en_envase[6], "")

        cal = [f for f in por_nombre[self.cal.name] if not f[9]][0]
        self.assertEqual(cal[1:4], ["1305-78-8", "CaO", "Solid"])
        self.assertEqual(cal[12], "02/01/2031")
        self.assertEqual(cal[10], 3)
        self.assertEqual(cal[8], 0)

    def test_documento_con_laboratorio_inexistente_y_sin_laboratorios(self):
        report = self.make_report("stock_reactive_report", "xlsx", laboratory=[self.lab.pk, 999999])
        with translation.override("es"):
            total = stock.report_stock(report)
            laboratorio = translation.gettext("Laboratory or work center")
            titulo = translation.gettext("Chemical substances inventory")
        filas = self.read_xlsx(report)
        self.assertEqual(len(filas) - 2, total)
        self.assertEqual(sum(1 for f in filas if f[0] == laboratorio), 1)
        self.assertIn(titulo, [f[0] for f in filas])

        todos = self.make_report("stock_reactive_report", "xlsx", laboratory=[])
        with translation.override("es"):
            stock.report_stock(todos)
        nombres = [f[1] for f in self.read_xlsx(todos) if f[0] == laboratorio]
        self.assertIn(self.lab.name, nombres)

    def test_documento_en_xls(self):
        self.assertIn("xls", dict(ReactiveStockReportForm.base_fields["format"].choices))
        report = self.make_report("stock_reactive_report", "xls", laboratory=[self.lab.pk])
        self.assertGreater(stock.report_stock(report), 0)
        report.refresh_from_db()
        with report.file.open("rb") as fh:
            hoja = xlrd.open_workbook(file_contents=fh.read()).sheet_by_index(0)
        self.assertGreater(hoja.nrows, 2)

    def test_cartel_html_agrupa_por_estado_fisico(self):
        report = self.make_report("chemicalinventory", "html")
        stock.report_reactive_stock_html(report)
        report.refresh_from_db()
        cal = [f for f in as_rows(report) if f["substance_name"] == self.cal.name]
        estados = {f["physical_status"] for f in cal}
        self.assertIn("Solid", estados)
        self.assertIn("", estados)
        self.assertEqual({f["in_where_laboratory__name"] for f in cal}, {self.lab.name})
        self.assertEqual({f["cas_id"] for f in cal}, {"1305-78-8"})

    def test_cartel_documento_varios_laboratorios(self):
        report = self.make_report("chemicalinventory", "xlsx", laboratory=[1, 2])
        total = stock.report_stock_cartel(report)
        filas = self.read_xlsx(report)
        self.assertEqual(len(filas) - 2, total)
        self.assertIn(self.cal.name, [f[1] for f in filas[2:]])

    def test_cartel_sin_laboratorios_usa_la_organizacion(self):
        report = self.make_report("chemicalinventory", "html", laboratory=[])
        self.assertGreater(stock.report_reactive_stock_html(report), 0)


class DiscardReportTest(ReportTestBase):
    """Objetos en estantes de desecho, filtrados por la fecha en que se crearon."""

    def setUp(self):
        super().setUp()
        self.cal = Object.objects.get(pk=2)
        desecho = Shelf.objects.get(pk=5)
        self.suelto = self.make_shelfobject(self.cal, shelf=desecho, quantity=3, created_by=self.user)
        self.caja = self.make_shelfobject(
            self.cal, shelf=desecho, quantity=2, is_box=True,
            quantity_units=[{"units": 4, "quantity": 1}, {"units": 6, "quantity": 1}],
        )
        self.viejo = self.make_shelfobject(self.cal, shelf=desecho, quantity=9)
        en_marzo = datetime(2024, 3, 10, 12, tzinfo=dt_timezone.utc)
        ShelfObject.objects.filter(pk__in=[self.suelto.pk, self.caja.pk]).update(creation_date=en_marzo)
        ShelfObject.objects.filter(pk=self.viejo.pk).update(
            creation_date=datetime(2023, 1, 1, tzinfo=dt_timezone.utc)
        )

    def report(self, file_type):
        return self.make_report(
            "report_waste_objects", file_type, period="01/03/2024 - 31/03/2024"
        )

    def test_html_filtra_por_periodo(self):
        report = self.report("html")
        self.assertEqual(discard_objects.report_discard_object_html(report), 2)
        report.refresh_from_db()
        filas = {f["quantity"]: f for f in as_rows(report)}
        # La caja multiplica las unidades por caja por la cantidad de cajas.
        self.assertEqual(set(filas), {"3.0", "20.0"})
        self.assertEqual(filas["3.0"]["created_by"], "admin")
        self.assertEqual(filas["20.0"]["created_by"], "Unknown")
        self.assertEqual(filas["3.0"]["creation_date"], "2024-03-10")

    def test_documento_filtra_por_periodo(self):
        report = self.report("xlsx")
        self.assertEqual(discard_objects.report_discard_object_doc(report), 2)
        filas = self.read_xlsx(report)
        datos = [f for f in filas if f[0] == "Quinto Estante"]
        self.assertEqual(sorted(f[3] for f in datos), ["20.0", "3.0"])
        self.assertIn("Unknown", [f[6] for f in datos])
