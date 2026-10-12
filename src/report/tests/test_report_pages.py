import io

import openpyxl
from django.urls import reverse

from laboratory.models import (
    Furniture,
    Laboratory,
    Object,
    PrecursorReport,
    PrecursorReportValues,
)
from report.tests.utils import XHR, ReportTestBase


class ReportPagesTest(ReportTestBase):
    """Pantallas de formulario de reporte: el contexto que arma cada una."""

    def get(self, urlname, params=None, org=None, **kwargs):
        kwargs.setdefault("org_pk", org or self.org.pk)
        return self.client.get(reverse("report:%s" % urlname, kwargs=kwargs), params or {}, **XHR)

    def test_tipo_de_objeto_invalido_es_404(self):
        self.assertEqual(self.get("reports_objects_list", {"type_id": "9"}).status_code, 404)
        self.assertEqual(self.get("reports_objects_list", {"type_id": "a"}).status_code, 404)

    def test_tipo_de_objeto_cambia_el_titulo(self):
        response = self.get("reports_objects_list", {"type_id": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.context["title_view"]), "Material Objects Report")
        self.assertEqual(response.context["form"].initial["object_type"], "1")

    def test_mueble_valido_precarga_el_formulario(self):
        mueble = Furniture.objects.get(pk=1)
        response = self.get("reports_furniture_detail", {"furniture": mueble.pk})
        self.assertEqual(response.status_code, 200)
        initial = response.context["form"].initial
        self.assertEqual(initial["furniture"], mueble)
        self.assertEqual(initial["lab_room"], mueble.labroom)
        self.assertEqual(initial["laboratory"], self.lab)

    def test_pagina_de_regencia(self):
        response = self.get("regency_report")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial["report_name"], "regency_report")

    def test_valores_de_precursor(self):
        response = self.get("precursor_report_values_view", precusor_pk=5)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["precusor_pk"], 5)
        self.assertEqual(response.context["form_create"].prefix, "create")

    def test_paginas_de_formulario(self):
        """Cada pantalla arma su formulario con el `report_name` del registro."""
        paginas = {
            "reports_limited_shelf_objects_list": "report_limit_objects",
            "reactive_precursor_object_list": "reactive_precursor",
            "object_change_logs": "report_objectschanges",
            "waste_report": "report_waste_objects",
            "reactive_report": "reactive_report",
            "risk_zone_report": "risk_zone_report",
            "reactive_stock_report": "stock_reactive_report",
            "compatibility_report": "compatibility_report",
            "hazard_map_report": "hazard_map_report",
        }
        for urlname, report_name in paginas.items():
            with self.subTest(urlname=urlname):
                response = self.get(urlname)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["form"].initial["report_name"], report_name)
                self.assertEqual(response.context["form"].initial["organization"], self.org.pk)

    def test_valores_de_precursor_sin_reporte(self):
        response = self.get("precursor_report_values_view", precusor_pk=0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["object_list"]), [])

    def test_donaciones(self):
        response = self.get("donations_report")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["object_list"]), [])
        self.assertEqual(response.context["form"].initial["report_name"], "donations_report")


class PrecursorsViewTest(ReportTestBase):
    def setUp(self):
        super().setUp()
        self.cal = Object.objects.get(pk=2)
        self.precursor = PrecursorReport.objects.create(
            month=3, month_belong=2, year=2024, laboratory=self.lab, consecutive=7
        )
        PrecursorReportValues.objects.create(
            precursor_report=self.precursor, object=self.cal,
            measurement_unit=self.unit(), previous_balance=10, new_income=5,
            stock=15, month_expense=4, final_balance=11, bills="F-1", providers="Prov",
        )
        PrecursorReportValues.objects.create(
            precursor_report=self.precursor, object=Object.objects.get(pk=1),
            measurement_unit=self.unit(), reason_to_spend="Docencia",
        )

    def url(self, org=None):
        return reverse("report:precursor_report", kwargs={"org_pk": org or self.org.pk})

    def test_filtra_por_laboratorio_elegido(self):
        otro = PrecursorReport.objects.create(
            month=4, month_belong=3, year=2024, laboratory=self.lab
        )
        # Como el navegador: el formulario envía también la organización (campo oculto).
        response = self.client.get(self.url(), {"laboratory": self.lab.pk, "organization": self.org.pk})
        self.assertEqual(list(response.context["datalist"]), [otro, self.precursor])

        por_defecto = self.client.get(self.url())
        self.assertIn(self.precursor, list(por_defecto.context["datalist"]))

        # El laboratorio 2 es de la organización pero el perfil no tiene rol en él.
        sin_rol = self.client.get(self.url(), {"laboratory": 2})
        self.assertEqual(list(sin_rol.context["datalist"]), [])

    def libro(self, pk):
        response = self.client.get(self.url(), {"format": "xlsx", "pk": pk})
        self.assertEqual(response.status_code, 200)
        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        return [list(r) for r in wb.worksheets[0].iter_rows(values_only=True)]

    def test_exporta_el_libro_del_mes(self):
        filas = self.libro(self.precursor.pk)
        self.assertIn("7", filas[0][0])
        self.assertIn("2024", filas[2][0])
        cal = [f for f in filas if f[0] == self.cal.name][0]
        # Saldo anterior, ingreso del mes, facturas, proveedor, existencias,
        # gasto y saldo final, en el orden de la cabecera.
        self.assertEqual(cal[1:10], [self.unit().description, 10, 5, "F-1", "Prov", 15, 4, 11, "N/A"])
        tanque = [f for f in filas if f[0] == "Tanque 1000 mL"][0]
        self.assertEqual(tanque[9], "Docencia")

    def test_precursor_de_otra_organizacion_no_se_exporta(self):
        ajeno_lab = Laboratory.objects.create(name="Ajeno", organization=self.foreign_org)
        ajeno = PrecursorReport.objects.create(
            month=3, month_belong=2, year=2024, laboratory=ajeno_lab
        )
        response = self.client.get(self.url(), {"format": "xlsx", "pk": ajeno.pk}, **XHR)
        self.assertEqual(response.status_code, 404)

    def test_sin_pk_el_libro_sale_vacio(self):
        response = self.client.get(self.url(), {"format": "xlsx"})
        self.assertEqual(response.status_code, 200)
