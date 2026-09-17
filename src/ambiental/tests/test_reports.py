import datetime
from decimal import Decimal

from django.test import override_settings
from django.urls import reverse

from ambiental import reports
from ambiental.ambiental_defaults import KEY_MEASURE_UNIT
from ambiental.forms import AmbientalReportForm
from ambiental.models import ConsumptionRecord
from ambiental.tests.base import AmbientalTestCase
from laboratory.models import Catalog
from report.models import TaskReport


class ReportTestCase(AmbientalTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.m3 = Catalog.objects.get(key=KEY_MEASURE_UNIT, description="m³")
        cls.kwh = Catalog.objects.get(key=KEY_MEASURE_UNIT, description="kWh")

    def setUp(self):
        super().setUp()
        self.water_point = self.make_point(code="AGUA")
        self.power_point = self.make_point(code="LUZ", resource_type=self.electricity)
        self.record(self.water_point, 1, "30", self.m3, total_cost="30000")
        self.record(self.water_point, 2, "45", self.m3, total_cost="45000")
        self.record(self.power_point, 1, "1000", self.kwh, total_cost="120000")
        other_point = self.make_point(organization=self.other_organization, building=self.other_building, code="AJENO")
        self.record(other_point, 1, "999", self.m3, organization=self.other_organization)

    def record(self, point, month, quantity, unit, organization=None, **kwargs):
        start = datetime.date(2026, month, 1)
        end = (start + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
        return ConsumptionRecord.objects.create(
            organization=organization or self.organization, point=point, period_start=start,
            period_end=end, quantity=Decimal(quantity), unit=unit, created_by=self.user, **kwargs
        )

    def make_report(self, name, file_type="html", **data):
        payload = {"organization": self.organization.pk, "name": "reporte", "title": "Reporte",
                   "report_name": name, "building": [], "resource_type": [], "period": ""}
        payload.update(data)
        return TaskReport.objects.create(
            created_by=self.user, type_report=name, status="On hold", file_type=file_type,
            data=payload, language="es",
        )


class ConsumptionReportsTest(ReportTestCase):

    def test_detail_only_includes_the_organization(self):
        report = self.make_report("report_consumption_detail")
        total = reports.report_consumption_detail_html(report)
        self.assertEqual(total, 3)
        codes = {row[1].split(" - ")[0] for row in report.table_content["dataset"]}
        self.assertEqual(codes, {"AGUA", "LUZ"})

    def test_filters_by_resource_and_period(self):
        report = self.make_report(
            "report_consumption_detail", resource_type=[self.water.pk], period="01/02/2026 - 28/02/2026"
        )
        self.assertEqual(reports.report_consumption_detail_html(report), 1)
        self.assertEqual(report.table_content["dataset"][0][5], "45")

    def test_summary_groups_by_month_and_unit(self):
        report = self.make_report("report_consumption_summary")
        reports.report_consumption_summary_html(report)
        rows = {(row[1], row[2]): row for row in report.table_content["dataset"]}
        self.assertEqual(rows[("Agua", "2026-01")][3], "30")
        self.assertEqual(rows[("Agua", "2026-02")][5], "45000")
        self.assertEqual(rows[("Electricidad", "2026-01")][4], "kWh")

    def test_cost_average(self):
        report = self.make_report("report_consumption_cost", resource_type=[self.electricity.pk])
        reports.report_consumption_cost_html(report)
        self.assertEqual(report.table_content["dataset"], [["Electricidad", "2026-01", "1000", "kWh", "120", "120000"]])

    @override_settings(MEDIA_ROOT="/tmp/organilab-test-media")
    def test_spreadsheet_is_generated(self):
        report = self.make_report("report_consumption_summary", file_type="xlsx")
        self.assertEqual(reports.report_consumption_summary_doc(report), 3)
        self.assertTrue(report.file.name.endswith(".xlsx"))

    def test_form_cleans_to_json_friendly_values(self):
        form = AmbientalReportForm(
            data={"name": "a", "title": "a", "organization": self.organization.pk,
                  "report_name": "report_consumption_detail", "format": "pdf",
                  "building": [self.building.pk], "resource_type": [self.water.pk]},
            org_pk=self.organization.pk, user=self.user,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["building"], [self.building.pk])
        form = AmbientalReportForm(
            data={"name": "a", "title": "a", "organization": self.organization.pk,
                  "report_name": "report_consumption_detail", "building": [self.other_building.pk]},
            org_pk=self.organization.pk, user=self.user,
        )
        self.assertFalse(form.is_valid())


class ReportPagesTest(ReportTestCase):

    def test_report_pages_render_for_each_role(self):
        names = ("ambiental:report_consumption_detail", "ambiental:report_consumption_summary",
                 "ambiental:report_consumption_cost")
        for rol_name in ("Administrador ambiental", "Encargado de registro ambiental", "Analista ambiental"):
            user = self.make_user("r_" + rol_name.split()[0], self.organization, rol_name)
            self.client.force_login(user)
            for name in names:
                with self.subTest(rol=rol_name, report=name):
                    response = self.client.get(reverse(name, kwargs={"org_pk": self.organization.pk}))
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, 'id="send"')


@override_settings(MEDIA_ROOT="/tmp/organilab-test-media")
class ReportQueueTest(ReportTestCase):
    """El reporte se pide por la cola común de `report` con un usuario con rol ambiental."""

    def test_analista_generates_the_summary(self):
        user = self.make_user("analista_q", self.organization, "Analista ambiental")
        self.client.force_login(user)
        response = self.client.get(
            reverse("report:create_report_request", kwargs={"org_pk": self.organization.pk}),
            {"name": "consolidado", "title": "Consolidado", "organization": self.organization.pk,
             "report_name": "report_consumption_summary", "format": "html",
             "resource_type": [self.water.pk]},
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json()["result"], response.content)
        task = TaskReport.objects.get(pk=response.json()["report"])
        self.assertEqual(len(task.table_content["dataset"]), 2)
