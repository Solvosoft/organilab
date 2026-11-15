"""Reportes de equipos (``laboratory/equipment/reports.py``): programa PT-05 y hoja de vida."""
import datetime
import io

from django.urls import reverse

from laboratory.equipment import importer
from laboratory.models import (
    EquipmentActivityPlan as Plan,
    ShelfObjectCalibrate,
    ShelfObjectEquipmentCharacteristics as Characteristics,
    ShelfObjectFailure,
    ShelfObjectMaintenance,
    Catalog,
)
from laboratory.tests.test_cov_api_equipment_records import RegistrosEquipoBase


class ReportesBase(RegistrosEquipoBase):

    def setUp(self):
        super().setUp()
        Characteristics.objects.filter(shelfobject=self.equipo).update(
            internal_code="LB-127", brand="Senderpick", model="KW-089", resolution="0.01",
            measurement_unit="gramos", physical_location="Mesa de balanzas",
        )
        Plan.objects.create(shelfobject=self.equipo, activity_kind=Plan.CALIBRATION, interval_value=12)
        Plan.objects.create(shelfobject=self.equipo, activity_kind=Plan.PREVENTIVE_MAINTENANCE, interval_value=12)
        ShelfObjectCalibrate.objects.create(
            shelfobject=self.equipo, calibration_date=datetime.date(2026, 4, 10), calibrate_name="Metrología",
            certificate_number="COC 051-2024", conformity="conforming",
        )
        mantenimiento = ShelfObjectMaintenance.objects.create(
            shelfobject=self.equipo, maintenance_date=datetime.date(2026, 3, 2), maintenance_type="preventive",
        )
        mantenimiento.activities.set(Catalog.objects.filter(key="maintenance_activity", description="Limpieza"))
        ShelfObjectFailure.objects.create(
            shelfobject=self.equipo, failure_date=datetime.date(2026, 5, 1), description="No enciende",
            blocked=False,
        )


class ProgramaExportadoTest(ReportesBase):

    def test_se_exporta_y_se_vuelve_a_leer(self):
        url = reverse("laboratory:equipment_program_export", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, {"year": 2026})
        self.assertEqual(response.status_code, 200)
        _sheet, rows = importer.read_workbook(io.BytesIO(response.content), importer.PROGRAM)
        fila = next(row for row in rows if row["internal_code"] == "LB-127")
        self.assertEqual(fila["brand"], "Senderpick")
        self.assertEqual(fila["resolution"], "0.01")
        self.assertEqual(fila["calibration_date"], "2026-04-10")
        self.assertEqual(fila["next_calibration_date"], "2027-04-10")
        self.assertEqual(fila["calibration_conformity"], "conforming")
        self.assertEqual(fila["maintenance"][0]["programmed_year"], 2026)
        self.assertEqual(fila["maintenance"][0]["activities"], ["Limpieza"])

    def test_las_consultas_no_crecen_con_los_equipos(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from laboratory.equipment.reports import program_workbook
        from laboratory.models import ShelfObject

        def consultas():
            with CaptureQueriesContext(connection) as capturadas:
                program_workbook(self.lab, 2026)
            return len(capturadas)

        antes = consultas()
        for numero in range(5):
            copia = ShelfObject.objects.get(pk=self.equipo.pk)
            copia.pk = None
            copia.shelfobject_code = None
            copia.save()
            Characteristics.objects.create(shelfobject=copia, internal_code="LB-9%02d" % numero)
            Plan.objects.create(shelfobject=copia, activity_kind=Plan.CALIBRATION, interval_value=12)
            ShelfObjectCalibrate.objects.create(shelfobject=copia, calibration_date=datetime.date(2026, 1, 1))
        self.assertEqual(consultas(), antes)

    def test_otro_laboratorio_no_exporta(self):
        ajeno, org_ajena = self.crear_usuario_ajeno()
        self.client.force_login(ajeno)
        url = reverse("laboratory:equipment_program_export", kwargs={"org_pk": org_ajena.pk, "lab_pk": self.lab.pk})
        self.assertEqual(self.client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest").status_code, 403)


class HojaDeVidaTest(ReportesBase):

    def url(self, pk=None, lab=None):
        return reverse("laboratory:equipment_life_record_pdf", kwargs={
            "org_pk": self.org.pk, "lab_pk": (lab or self.lab).pk, "pk": pk or self.equipo.pk,
        })

    def test_pdf_con_todas_las_secciones(self):
        from laboratory.equipment.reports import life_record_context
        from django.template.loader import get_template

        html = get_template("laboratory/equipment/life_record_pdf.html").render(
            dict(life_record_context(self.equipo), title="Hoja de vida")
        )
        for texto in ("LB-127", "Senderpick", "COC 051-2024", "Limpieza", "No enciende", "Mesa de balanzas"):
            self.assertIn(texto, html)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertIn("hoja_de_vida_LB-127.pdf", response["Content-Disposition"])

    def test_equipo_de_otro_laboratorio(self):
        from laboratory.models import Laboratory

        response = self.client.get(self.url(lab=Laboratory.objects.get(pk=2)), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 404)

    def test_un_reactivo_no_tiene_hoja_de_vida(self):
        from laboratory.models import ShelfObject

        reactivo = ShelfObject.objects.filter(in_where_laboratory=self.lab, object__type="0").first()
        self.assertEqual(self.client.get(self.url(pk=reactivo.pk), HTTP_X_REQUESTED_WITH="XMLHttpRequest").status_code, 404)
