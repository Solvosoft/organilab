"""Forma de las consultas de los reportes: que no crezcan con los datos.

Los reportes recorrían miles de filas con media docena de consultas cada una
(objeto, unidad, estante, ficha SGA, códigos H, conversión de unidades...) y a
escala real no terminaban. Lo que se prueba no es un número bonito sino que el
costo **no depende del inventario**: agregar filas no puede agregar consultas.

Cada prueba cuenta las consultas de un reporte, multiplica el inventario y
vuelve a contar. Antes de medir se corre una vez el reporte para calentar las
cachés de ContentType, que también cuentan.
"""

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from laboratory.models import (
    Catalog,
    Furniture,
    Object,
    ObjectLogChange,
    Shelf,
    ShelfObject,
    ShelfObjectLimits,
)
from report.tests.utils import ReportTestBase
from report.views import donation, furniture, lab_room, objects, reactive, stock
from report.views.object_changes import get_dataset_objectlogchanges
from sga.models import DangerIndication, HCodeCategory, SubstanceCharacteristics


class ReportQueryShapeTest(ReportTestBase):

    def setUp(self):
        super().setUp()
        self.codes = list(DangerIndication.objects.order_by("code")[:3])
        for code, category in zip(self.codes, ("physical", "health", "environment")):
            HCodeCategory.objects.create(danger_category=category).h_code.add(code)
        self.shelves = list(Shelf.objects.filter(furniture__labroom__laboratory=self.lab))
        self.assertTrue(self.shelves, "el fixture debería traer estantes en el laboratorio")
        self.batch = 0

    # -- datos ---------------------------------------------------------------

    def grow(self, how_many=12):
        """Reactivos nuevos con ficha SGA, códigos H y unidades distintas."""
        self.batch += 1
        units = list(Catalog.objects.filter(key="units", unit__isnull=False)[:3])
        for index in range(how_many):
            obj = Object.objects.create(
                code="VOL-%d-%d" % (self.batch, index),
                name="Reactivo %d-%d" % (self.batch, index),
                type=Object.REACTIVE,
                is_pure=True,
                organization=self.org,
            )
            sga = SubstanceCharacteristics.objects.create(
                object_related=obj, cas_id_number="50-00-%d" % index, is_precursor=True
            )
            sga.h_code.set(self.codes)
            shelf = self.shelves[index % len(self.shelves)]
            unit = units[index % len(units)]
            ShelfObject.objects.create(
                object=obj,
                shelf=shelf,
                quantity=index + 1,
                measurement_unit=unit,
                in_where_laboratory=self.lab,
                physical_status="liquid" if index % 2 else None,
                was_donated=bool(index % 3 == 0),
                limits=ShelfObjectLimits.objects.create(
                    minimum_limit=0, maximum_limit=index + 1
                ),
            )
            ObjectLogChange.objects.create(
                object=obj,
                laboratory=self.lab,
                user=self.user,
                old_value=0,
                new_value=index + 1,
                diff_value=index + 1,
                measurement_unit=unit,
                precursor=True,
            )

    def count(self, run):
        with CaptureQueriesContext(connection) as captured:
            run()
        return len(captured)

    def assertConstant(self, run):
        run()  # calienta cachés de ContentType y similares
        before = self.count(run)
        self.grow()
        after_first = self.count(run)
        self.grow()
        after_second = self.count(run)
        self.assertEqual(
            after_first, after_second,
            "las consultas crecen con el inventario: %d -> %d -> %d"
            % (before, after_first, after_second),
        )

    def report_runner(self, function, type_report, file_type="html", **data):
        def run():
            report = self.make_report(type_report, file_type, **data)
            function(report)
        return run

    # -- reportes ------------------------------------------------------------

    def test_inventario_por_sala(self):
        self.assertConstant(
            self.report_runner(lab_room.lab_room_html, "report_laboratory_room")
        )

    def test_inventario_por_mueble(self):
        furniture_pks = list(
            Furniture.objects.filter(labroom__laboratory=self.lab).values_list("pk", flat=True)
        )
        self.assertConstant(
            self.report_runner(
                furniture.furniture_html, "report_furniture",
                furniture=furniture_pks, object_type="1",
            )
        )

    def test_reactivos_por_mueble(self):
        furniture_pks = list(
            Furniture.objects.filter(labroom__laboratory=self.lab).values_list("pk", flat=True)
        )
        self.assertConstant(
            self.report_runner(
                furniture.furniture_html, "report_furniture",
                furniture=furniture_pks, object_type="0", is_precursor=True,
            )
        )

    def test_objetos(self):
        self.assertConstant(
            self.report_runner(
                objects.report_objects_html, "report_objects", object_type="0"
            )
        )

    def test_limites(self):
        self.assertConstant(
            self.report_runner(objects.report_limit_object_html, "report_limit_objects")
        )

    def test_reactivos(self):
        self.assertConstant(
            self.report_runner(reactive.report_reactive_html, "reactive_report")
        )

    def test_donaciones(self):
        self.assertConstant(
            self.report_runner(donation.report_donations_html, "donations_report")
        )

    def test_cartel_de_inventario(self):
        self.assertConstant(
            self.report_runner(stock.report_reactive_stock_html, "chemicalinventory")
        )

    def test_existencias(self):
        self.assertConstant(lambda: stock.get_stock_dataset(self.lab.pk))

    def test_cambios_de_objetos(self):
        today = timezone.now().strftime("%d/%m/%Y")
        period = "%s - %s" % (today, today)
        self.assertConstant(
            self.report_runner(
                lambda report: get_dataset_objectlogchanges(report),
                "report_objectschanges", period=period, precursor=True,
            )
        )
        self.assertConstant(
            self.report_runner(
                lambda report: get_dataset_objectlogchanges(report, True),
                "report_objectschanges", "xlsx", period=period, precursor=True,
            )
        )


class StockDatasetTest(ReportTestBase):
    """Las existencias dan una fila por reactivo, no una por cada unidad."""

    def test_sin_filas_repetidas(self):
        obj = Object.objects.create(
            code="DUP-1", name="Duplicado", type=Object.REACTIVE, organization=self.org
        )
        SubstanceCharacteristics.objects.create(object_related=obj)
        for quantity in (1, 2, 3):
            self.make_shelfobject(obj, quantity=quantity)
        rows = [row for row in stock.get_stock_dataset(self.lab.pk) if row[0] == obj.name]
        self.assertEqual(len(rows), 1)
