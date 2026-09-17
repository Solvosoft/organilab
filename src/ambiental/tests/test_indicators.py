import datetime
from decimal import Decimal

from django.urls import reverse

from ambiental import reports
from ambiental.ambiental_defaults import KEY_NORMALIZER, NORMALIZER_AREA, NORMALIZER_PERSON
from ambiental.forms import ComparisonReportForm
from ambiental.indicators import compare_periods, compute_indicator, variation
from ambiental.models import ConsumptionRecord, NormalizationBase
from ambiental.tests.test_reports import ReportTestCase
from laboratory.models import Catalog

JAN = (datetime.date(2026, 1, 1), datetime.date(2026, 1, 31))
FEB = (datetime.date(2026, 2, 1), datetime.date(2026, 2, 28))
YEAR = (datetime.date(2026, 1, 1), datetime.date(2026, 12, 31))


class IndicatorTest(ReportTestCase):

    def setUp(self):
        super().setUp()
        self.area = Catalog.objects.get(key=KEY_NORMALIZER, description=NORMALIZER_AREA)
        self.person = Catalog.objects.get(key=KEY_NORMALIZER, description=NORMALIZER_PERSON)
        NormalizationBase.objects.create(
            organization=self.organization, building=self.building, normalizer=self.person,
            year=2025, value=Decimal("25"),
        )

    def test_indicator_divides_by_inherited_base(self):
        result = compute_indicator(self.organization, self.building, self.water, self.person, *YEAR)
        self.assertEqual(result["raw_total"], Decimal("75"))
        self.assertEqual(result["base"], Decimal("25"))
        self.assertEqual(result["base_year"], 2025)
        self.assertEqual(result["value"], Decimal("3.0000"))

    def test_missing_base_gives_no_value(self):
        result = compute_indicator(self.organization, self.building, self.water, self.area, *YEAR)
        self.assertIsNone(result["value"])
        self.assertEqual(result["raw_total"], Decimal("75"))

    def test_mixed_units_are_not_added(self):
        self.record(self.water_point, 3, "5000", Catalog.objects.get(key="ambiental_measure_unit", description="L"))
        result = compute_indicator(self.organization, self.building, self.water, self.person, *YEAR)
        self.assertTrue(result["mixed_units"])
        self.assertIsNone(result["value"])

    def test_record_counts_in_month_of_period_end(self):
        # Un recibo del 15 de enero al 14 de febrero cuenta en febrero.
        self.record(self.water_point, 3, "1", self.m3)  # marzo, fuera de rango
        point = self.make_point(code="OTRO")
        ConsumptionRecord.objects.create(
            organization=self.organization, point=point, period_start=datetime.date(2026, 1, 15),
            period_end=datetime.date(2026, 2, 14), quantity=Decimal("10"), unit=self.m3,
        )
        january, february = compare_periods(self.organization, self.water, [JAN, FEB], self.building)
        self.assertEqual(january["quantity"], Decimal("30"))
        self.assertEqual(february["quantity"], Decimal("55"))

    def test_variation(self):
        january, february = compare_periods(self.organization, self.water, [JAN, FEB])
        self.assertEqual(february["absolute"], Decimal("15"))
        self.assertEqual(february["percent"], Decimal("50.00"))
        self.assertEqual(february["cost"], Decimal("45000"))
        self.assertIsNone(january["percent"])
        self.assertEqual(variation(Decimal(0), Decimal(5)), {"absolute": Decimal(5), "percent": None})

    def test_indicator_report(self):
        report = self.make_report(
            "report_environmental_indicators", period="01/01/2026 - 31/12/2026",
            normalizer=[self.person.pk],
        )
        reports.report_environmental_indicators_html(report)
        rows = {row[1]: row for row in report.table_content["dataset"]}
        self.assertEqual(rows["Agua"][7], "3")
        self.assertEqual(rows["Electricidad"][7], "40")

    def test_comparison_report(self):
        report = self.make_report(
            "report_consumption_comparison", comparison_period="01/01/2026 - 31/01/2026",
            period="01/02/2026 - 28/02/2026", resource_type=[self.water.pk],
        )
        reports.report_consumption_comparison_html(report)
        self.assertEqual(report.table_content["dataset"], [
            ["Edificio A", "Agua", "30", "45", "m³", "15", "50", "30000", "45000"],
        ])

    def test_comparison_form_requires_both_periods(self):
        form = ComparisonReportForm(
            data={"name": "a", "title": "a", "organization": self.organization.pk,
                  "report_name": "report_consumption_comparison", "period": "01/02/2026 - 28/02/2026"},
            org_pk=self.organization.pk, user=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("comparison_period", form.errors)

    def test_pages_render(self):
        for name in ("report_environmental_indicators", "report_consumption_comparison"):
            for rol_name in ("Administrador ambiental", "Encargado de registro ambiental", "Analista ambiental"):
                user = self.make_user("i_%s_%s" % (name[-5:], rol_name.split()[0]), self.organization, rol_name)
                self.client.force_login(user)
                with self.subTest(report=name, rol=rol_name):
                    response = self.client.get(reverse("ambiental:" + name, kwargs={"org_pk": self.organization.pk}))
                    self.assertEqual(response.status_code, 200)
