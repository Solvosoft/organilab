import json
from decimal import Decimal

from django.urls import reverse

from ambiental.ambiental_defaults import KEY_NORMALIZER, NORMALIZER_AREA, NORMALIZER_PERSON
from ambiental.models import NormalizationBase
from ambiental.normalization import building_people, get_base, preload_bases
from ambiental.tests.base import AmbientalTestCase
from laboratory.models import Catalog, Laboratory
from risk_management.models import RiskZone, Workday, ZoneType


class NormalizationTestCase(AmbientalTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.area = Catalog.objects.get(key=KEY_NORMALIZER, description=NORMALIZER_AREA)
        cls.person = Catalog.objects.get(key=KEY_NORMALIZER, description=NORMALIZER_PERSON)
        cls.second_lab = Laboratory.objects.create(name="Laboratorio de Física", organization=cls.organization)
        cls.building.laboratories.add(cls.second_lab)
        zone_type = ZoneType.objects.create(name="Laboratorio")
        # Una zona que cubre los dos laboratorios del edificio: sus jornadas no se
        # pueden contar dos veces.
        cls.zone = RiskZone.objects.create(
            name="Zona compartida", organization=cls.organization, zone_type=zone_type,
            priority=1, num_workers=0,
        )
        cls.zone.laboratories.add(cls.laboratory, cls.second_lab)
        for workers in (10, 5):
            Workday.objects.create(
                workday="day shift", num_workers=workers, start_time="07:00",
                end_time="15:00", risk_zone=cls.zone, organization=cls.organization,
            )


class PreloadTest(NormalizationTestCase):

    def test_people_are_counted_once_per_workday(self):
        self.assertEqual(building_people(self.building), Decimal(15))

    def test_preload_creates_area_and_people(self):
        result = preload_bases(self.organization, 2026)
        self.assertEqual(len(result["created"]), 2)
        self.assertEqual(
            NormalizationBase.objects.get(building=self.building, normalizer=self.area, year=2026).value,
            Decimal("1200.00"),
        )
        people = NormalizationBase.objects.get(building=self.building, normalizer=self.person, year=2026)
        self.assertEqual(people.value, Decimal("15"))
        self.assertFalse(people.is_manual)

    def test_preload_keeps_manual_values_and_updates_deduced_ones(self):
        preload_bases(self.organization, 2026)
        manual = NormalizationBase.objects.get(building=self.building, normalizer=self.area, year=2026)
        manual.value, manual.is_manual = Decimal("900"), True
        manual.save()
        self.building.area = 1500
        self.building.save()
        Workday.objects.filter(risk_zone=self.zone).update(num_workers=20)

        result = preload_bases(self.organization, 2026)

        manual.refresh_from_db()
        self.assertEqual(manual.value, Decimal("900"))
        self.assertEqual(len(result["updated"]), 1)
        self.assertEqual(
            NormalizationBase.objects.get(building=self.building, normalizer=self.person, year=2026).value,
            Decimal("40"),
        )

    def test_building_without_data_is_skipped(self):
        self.building.area = 0
        self.building.save()
        Workday.objects.all().delete()
        result = preload_bases(self.organization, 2026)
        self.assertEqual(result["created"], [])
        self.assertEqual(result["skipped"], 2)

    def test_missing_year_inherits_previous_base(self):
        NormalizationBase.objects.create(
            organization=self.organization, building=self.building, normalizer=self.area,
            year=2024, value=Decimal("800"),
        )
        base = get_base(self.organization, self.building, self.area, 2026)
        self.assertEqual(base.year, 2024)
        self.assertIsNone(get_base(self.organization, self.building, self.area, 2023))


class NormalizationBaseAPITest(NormalizationTestCase):

    def url(self, name, **kwargs):
        return reverse("ambiental:api-normalizationbase-" + name, kwargs={"org_pk": self.organization.pk, **kwargs})

    def test_preload_action(self):
        response = self.client.post(self.url("preload"), data=json.dumps({"year": 2026}), content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["created"], 2)
        data = self.client.get(self.url("list")).json()
        self.assertEqual(data["recordsTotal"], 2)

    def test_manual_edit_marks_as_manual(self):
        preload_bases(self.organization, 2026)
        base = NormalizationBase.objects.get(building=self.building, normalizer=self.area, year=2026)
        response = self.client.put(
            self.url("detail", pk=base.pk),
            data=json.dumps({"building": self.building.pk, "normalizer": self.area.pk, "year": 2026, "value": "950"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        base.refresh_from_db()
        self.assertTrue(base.is_manual)
        self.assertEqual(base.value, Decimal("950"))

    def test_duplicate_year_is_rejected(self):
        preload_bases(self.organization, 2026)
        response = self.client.post(
            self.url("list"),
            data=json.dumps({"building": self.building.pk, "normalizer": self.area.pk, "year": 2026, "value": "1"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("year", response.json())

    def test_registro_role_cannot_preload(self):
        user = self.make_user("registro", self.organization, "Encargado de registro ambiental")
        self.client.force_login(user)
        response = self.client.post(self.url("preload"), data=json.dumps({"year": 2026}), content_type="application/json")
        self.assertEqual(response.status_code, 403)

    def test_page_renders_for_each_role(self):
        for rol_name in ("Administrador ambiental", "Encargado de registro ambiental", "Analista ambiental"):
            with self.subTest(rol=rol_name):
                user = self.make_user("n_" + rol_name.split()[0], self.organization, rol_name)
                self.client.force_login(user)
                response = self.client.get(
                    reverse("ambiental:normalizationbase_list", kwargs={"org_pk": self.organization.pk})
                )
                self.assertEqual(response.status_code, 200)
