import datetime
import json
from decimal import Decimal

from django.core.files.base import ContentFile
from django.utils import formats
from django.test import override_settings
from django.urls import reverse
from djgentelella.models import ChunkedUpload

from ambiental.ambiental_defaults import (
    KEY_MEASURE_UNIT,
    KEY_RESOURCE_TYPE,
    KEY_WASTE_TREATMENT,
    RESOURCE_FUEL,
    RESOURCE_HAZARDOUS_WASTE,
)
from ambiental.models import ConsumptionRecord
from ambiental.tests.base import AmbientalTestCase
from laboratory.models import Catalog, Provider


def chunked_token(user, name="recibo.pdf"):
    upload = ChunkedUpload.objects.create(user=user, filename=name, offset=4, status=2)
    upload.file.save(name, ContentFile(b"%PDF"), save=True)
    return json.dumps({"token": str(upload.upload_id)})


class ConsumptionRecordModelTest(AmbientalTestCase):

    def make_record(self, **kwargs):
        defaults = dict(
            organization=self.organization,
            point=self.make_point(),
            period_start=datetime.date(2026, 1, 1),
            period_end=datetime.date(2026, 1, 31),
            quantity=Decimal("40"),
            unit=Catalog.objects.get(key=KEY_MEASURE_UNIT, description="m³"),
        )
        defaults.update(kwargs)
        return ConsumptionRecord.objects.create(**defaults)

    def test_total_cost_is_computed_from_unit_cost(self):
        record = self.make_record(unit_cost=Decimal("1250.5"))
        self.assertEqual(record.total_cost, Decimal("50020.00"))

    def test_unit_cost_is_computed_from_total_cost(self):
        record = self.make_record(total_cost=Decimal("100"), quantity=Decimal("3"))
        self.assertEqual(record.unit_cost, Decimal("33.3333"))

    def test_waste_resource_forces_is_waste(self):
        waste = Catalog.objects.get(key=KEY_RESOURCE_TYPE, description=RESOURCE_HAZARDOUS_WASTE)
        record = self.make_record(point=self.make_point(code="ACOPIO", resource_type=waste))
        self.assertTrue(record.is_waste)


@override_settings(MEDIA_ROOT="/tmp/organilab-test-media")
class ConsumptionRecordAPITest(AmbientalTestCase):

    def setUp(self):
        super().setUp()
        self.point = self.make_point()
        self.m3 = Catalog.objects.get(key=KEY_MEASURE_UNIT, description="m³")

    def list_url(self, organization=None):
        return reverse(
            "ambiental:api-consumptionrecord-list",
            kwargs={"org_pk": (organization or self.organization).pk},
        )

    def detail_url(self, record):
        return reverse(
            "ambiental:api-consumptionrecord-detail",
            kwargs={"org_pk": self.organization.pk, "pk": record.pk},
        )

    def payload(self, **kwargs):
        data = {
            "point": self.point.pk,
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
            "quantity": "38.5",
            "unit_cost": "1000",
            "note": "Recibo de enero",
        }
        data.update(kwargs)
        return data

    def post(self, data):
        return self.client.post(self.list_url(), data=json.dumps(data), content_type="application/json")

    def test_create_fills_unit_and_costs(self):
        response = self.post(self.payload(document=chunked_token(self.user)))
        self.assertEqual(response.status_code, 201, response.content)
        record = ConsumptionRecord.objects.get(point=self.point)
        self.assertEqual(record.unit, self.m3)
        self.assertEqual(record.total_cost, Decimal("38500.00"))
        self.assertEqual(record.organization, self.organization)
        self.assertTrue(record.document.name)
        self.assertFalse(record.is_waste)

    def test_period_end_before_start_is_rejected(self):
        response = self.post(self.payload(period_start="2026-01-31", period_end="2026-01-01"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("period_end", response.json())

    def test_overlapping_period_is_rejected(self):
        self.assertEqual(self.post(self.payload()).status_code, 201)
        response = self.post(self.payload(period_start="2026-01-15", period_end="2026-02-14"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("period_start", response.json())

    def test_next_period_is_allowed(self):
        self.assertEqual(self.post(self.payload()).status_code, 201)
        response = self.post(self.payload(period_start="2026-02-01", period_end="2026-02-28"))
        self.assertEqual(response.status_code, 201, response.content)

    def test_update_does_not_overlap_with_itself(self):
        self.assertEqual(self.post(self.payload()).status_code, 201)
        record = ConsumptionRecord.objects.get(point=self.point)
        response = self.client.put(
            self.detail_url(record),
            data=json.dumps(self.payload(quantity="40", unit_cost="", total_cost="80000")),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        record.refresh_from_db()
        self.assertEqual(record.quantity, Decimal("40"))

    def test_extra_fields_are_kept_only_for_their_resource(self):
        fuel = Catalog.objects.get(key=KEY_RESOURCE_TYPE, description=RESOURCE_FUEL)
        fuel_point = self.make_point(code="PLACA", resource_type=fuel)
        response = self.post(self.payload(
            point=fuel_point.pk, vehicle_plate=" CL-1234 ", waste_code="no aplica",
        ))
        self.assertEqual(response.status_code, 201, response.content)
        record = ConsumptionRecord.objects.get(point=fuel_point)
        self.assertEqual(record.extra_data, {"vehicle_plate": "CL-1234"})
        self.assertEqual(record.unit.description, "L")

    def test_waste_record_keeps_treatment_and_manager(self):
        waste = Catalog.objects.get(key=KEY_RESOURCE_TYPE, description=RESOURCE_HAZARDOUS_WASTE)
        point = self.make_point(code="ACOPIO", resource_type=waste)
        treatment = Catalog.objects.get(key=KEY_WASTE_TREATMENT, description="Incineración")
        manager = Provider.objects.create(name="Gestor autorizado S.A.", laboratory=self.laboratory)
        response = self.post(self.payload(
            point=point.pk, treatment=treatment.pk, waste_manager=manager.pk,
            manifest_number="M-77",
        ))
        self.assertEqual(response.status_code, 201, response.content)
        record = ConsumptionRecord.objects.get(point=point)
        self.assertTrue(record.is_waste)
        self.assertEqual(record.treatment, treatment)
        self.assertEqual(record.waste_manager, manager)
        self.assertEqual(record.extra_data, {"manifest_number": "M-77"})

    def test_point_of_other_organization_is_rejected(self):
        foreign = self.make_point(
            organization=self.other_organization, building=self.other_building, code="X"
        )
        response = self.post(self.payload(point=foreign.pk))
        self.assertEqual(response.status_code, 400)
        self.assertIn("point", response.json())

    def test_list_filters_by_building_and_serializes_extra_fields(self):
        self.assertEqual(self.post(self.payload()).status_code, 201)
        response = self.client.get(self.list_url(), {"point__building": self.building.pk})
        data = response.json()
        self.assertEqual(data["recordsFiltered"], 1)
        row = data["data"][0]
        self.assertEqual(row["building"]["text"], "Edificio A")
        self.assertEqual(row["resource_info"]["unit"]["id"], self.m3.pk)
        self.assertEqual(
            row["period_start"],
            datetime.date(2026, 1, 1).strftime(formats.get_format("DATE_INPUT_FORMATS")[0]),
        )
        response = self.client.get(self.list_url(), {"point__building": self.other_building.pk})
        self.assertEqual(response.json()["recordsFiltered"], 0)

    def test_destroy_goes_to_trash(self):
        self.assertEqual(self.post(self.payload()).status_code, 201)
        record = ConsumptionRecord.objects.get(point=self.point)
        self.assertEqual(self.client.delete(self.detail_url(record)).status_code, 204)
        self.assertTrue(ConsumptionRecord.objects_deleted_only.filter(pk=record.pk).exists())
        # El período borrado bloquea duplicarlo: hay que restaurarlo desde la papelera.
        self.assertEqual(self.post(self.payload()).status_code, 400)

    def test_registro_role_records_but_does_not_configure_points(self):
        user = self.make_user("registro", self.organization, "Encargado de registro ambiental")
        self.client.force_login(user)
        self.assertEqual(self.post(self.payload()).status_code, 201)
        response = self.client.post(
            reverse("ambiental:api-measurementpoint-list", kwargs={"org_pk": self.organization.pk}),
            data=json.dumps({"code": "N", "name": "N"}), content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_analista_role_is_read_only(self):
        user = self.make_user("analista", self.organization, "Analista ambiental")
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.list_url()).status_code, 200)
        self.assertEqual(self.post(self.payload()).status_code, 403)

    def test_point_select_carries_resource_info(self):
        response = self.client.get(
            reverse("ambiental_points-list"),
            {"org_pk": self.organization.pk, "building": self.building.pk},
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()["results"][0]
        self.assertEqual(result["resource_info"]["unit"]["text"], "m³")


class ConsumptionRecordViewTest(AmbientalTestCase):

    def test_page_renders_for_each_role(self):
        for rol_name in ("Administrador ambiental", "Encargado de registro ambiental", "Analista ambiental"):
            with self.subTest(rol=rol_name):
                user = self.make_user("u_" + rol_name.split()[0], self.organization, rol_name)
                self.client.force_login(user)
                response = self.client.get(
                    reverse("ambiental:consumptionrecord_list", kwargs={"org_pk": self.organization.pk})
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "table-consumptionrecord")
