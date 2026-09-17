import datetime
from decimal import Decimal

from django.urls import reverse

from ambiental import reports
from ambiental.ambiental_defaults import (
    KEY_RESOURCE_TYPE,
    KEY_WASTE_TREATMENT,
    RESOURCE_HAZARDOUS_WASTE,
)
from ambiental.models import ConsumptionRecord
from ambiental.tests.test_reports import ReportTestCase
from laboratory.models import Catalog, Provider


class WasteTest(ReportTestCase):

    def setUp(self):
        super().setUp()
        hazardous = Catalog.objects.get(key=KEY_RESOURCE_TYPE, description=RESOURCE_HAZARDOUS_WASTE)
        self.waste_point = self.make_point(code="ACOPIO", resource_type=hazardous)
        self.kg = Catalog.objects.get(key="ambiental_measure_unit", description="kg")
        ConsumptionRecord.objects.create(
            organization=self.organization, point=self.waste_point,
            period_start=datetime.date(2026, 3, 1), period_end=datetime.date(2026, 3, 10),
            quantity=Decimal("12.5"), unit=self.kg,
            treatment=Catalog.objects.get(key=KEY_WASTE_TREATMENT, description="Incineración"),
            waste_manager=Provider.objects.create(name="Gestor S.A.", laboratory=self.laboratory),
            extra_data={"manifest_number": "M-1", "waste_code": "R-01"},
        )

    def test_manifest_report_only_includes_waste(self):
        report = self.make_report("report_waste_manifest")
        self.assertEqual(reports.report_waste_manifest_html(report), 1)
        row = report.table_content["dataset"][0]
        self.assertEqual(row[2], RESOURCE_HAZARDOUS_WASTE)
        self.assertEqual(row[6:10], ["Incineración", "Gestor S.A.", "R-01", "M-1"])

    def test_point_select_splits_waste_and_consumption(self):
        url = reverse("ambiental_points-list")
        waste = self.client.get(url, {"org_pk": self.organization.pk, "waste": "1"}).json()["results"]
        consumption = self.client.get(url, {"org_pk": self.organization.pk, "waste": "0"}).json()["results"]
        self.assertEqual([row["id"] for row in waste], [self.waste_point.pk])
        self.assertNotIn(self.waste_point.pk, [row["id"] for row in consumption])
        self.assertEqual(len(consumption), 2)

    def test_api_filters_waste_records(self):
        url = reverse("ambiental:api-consumptionrecord-list", kwargs={"org_pk": self.organization.pk})
        self.assertEqual(self.client.get(url, {"is_waste": "true"}).json()["recordsFiltered"], 1)
        self.assertEqual(self.client.get(url, {"is_waste": "false"}).json()["recordsFiltered"], 3)

    def test_pages_render_for_each_role(self):
        for rol_name in ("Administrador ambiental", "Encargado de registro ambiental", "Analista ambiental"):
            user = self.make_user("w_" + rol_name.split()[0], self.organization, rol_name)
            self.client.force_login(user)
            for name in ("waste_list", "report_waste_manifest"):
                with self.subTest(rol=rol_name, page=name):
                    response = self.client.get(reverse("ambiental:" + name, kwargs={"org_pk": self.organization.pk}))
                    self.assertEqual(response.status_code, 200)
