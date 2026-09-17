import datetime
import json
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory
from django.urls import reverse

from ambiental import reports
from ambiental.access import BuildingAccess
from ambiental.alerts import evaluate_rule
from ambiental.models import ConsumptionAlert, ConsumptionRecord, NormalizationBase
from ambiental.tests.test_reports import ReportTestCase
from auth_and_perms.api.viewsets import DeleteUserFromContenttypeViewSet
from auth_and_perms.models import Profile, ProfilePermission, Rol
from laboratory.models import Catalog, UserOrganization
from presentation.alerts import KEY_ALERT_TRIGGER, TRIGGER_PERCENT
from presentation.models import AlertEvent, AlertRule
from risk_management.models import Buildings


class BuildingAccessTestCase(ReportTestCase):
    """Edificio A (el de la base, con agua y luz) y edificio B con su propio punto."""

    def setUp(self):
        super().setUp()
        self.building_b = Buildings.objects.create(name="Edificio B", phone="", organization=self.organization)
        self.point_b = self.make_point(building=self.building_b, code="AGUA-B")
        self.record_b = self.record(self.point_b, 1, "10", self.m3)

    def building_user(self, username, roles):
        """Usuario de la organización **sin rol de organización**, solo roles por edificio."""
        from django.contrib.auth.models import User

        user = User.objects.create_user(username=username, password="pass", email="%s@example.com" % username)
        profile = Profile.objects.create(user=user)
        UserOrganization.objects.create(user=user, organization=self.organization, type_in_organization=3, status=True)
        for building, rol_name in roles.items():
            permission = ProfilePermission.objects.create(
                profile=profile, organization=self.organization,
                content_type=ContentType.objects.get_for_model(Buildings), object_id=building.pk,
            )
            permission.rol.add(Rol.objects.get(name=rol_name))
        return user

    def url(self, name, **kwargs):
        return reverse("ambiental:" + name, kwargs={"org_pk": self.organization.pk, **kwargs})

    def post(self, name, data, **kwargs):
        return self.client.post(self.url(name, **kwargs), data=json.dumps(data), content_type="application/json")

    def put(self, name, data, **kwargs):
        return self.client.put(self.url(name, **kwargs), data=json.dumps(data), content_type="application/json")


class OrganizationRoleTest(BuildingAccessTestCase):

    def test_organization_role_sees_every_building(self):
        data = self.client.get(self.url("api-measurementpoint-list")).json()
        self.assertEqual(data["recordsTotal"], 3)
        access = BuildingAccess(self.user, self.organization)
        self.assertIsNone(access.building_ids("ambiental.view_consumptionrecord"))
        self.assertTrue(access.has("ambiental.change_consumptionrecord", self.building_b))
        # Pero nunca un edificio de otra organización.
        self.assertFalse(access.has("ambiental.change_consumptionrecord", self.other_building))


class MixedBuildingRolesTest(BuildingAccessTestCase):
    """Administrador ambiental en A y analista en B."""

    def setUp(self):
        super().setUp()
        self.mixed = self.building_user("mixto", {
            self.building: "Administrador ambiental", self.building_b: "Analista ambiental",
        })
        self.client.force_login(self.mixed)

    def point_payload(self, building, code):
        return {"code": code, "name": "Nuevo", "point_type": self.meter.pk, "resource_type": self.water.pk,
                "building": building.pk, "laboratories": [], "meters_count": 1}

    def test_page_opens_with_only_building_roles(self):
        response = self.client.get(self.url("consumptionrecord_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("ambiental:measurementpoint_list", kwargs={"org_pk": self.organization.pk}))

    def test_lists_both_buildings_with_actions_by_building(self):
        rows = self.client.get(self.url("api-consumptionrecord-list")).json()["data"]
        by_building = {row["building"]["text"]: row["actions"] for row in rows}
        self.assertEqual(set(by_building), {"Edificio A", "Edificio B"})
        self.assertTrue(by_building["Edificio A"]["update"])
        self.assertFalse(by_building["Edificio B"]["update"])
        self.assertFalse(by_building["Edificio B"]["destroy"])

    def test_creates_in_admin_building_only(self):
        self.assertEqual(self.post("api-measurementpoint-list", self.point_payload(self.building, "N-A")).status_code, 201)
        self.assertEqual(self.post("api-measurementpoint-list", self.point_payload(self.building_b, "N-B")).status_code, 403)

    def test_cannot_edit_delete_or_move_into_analyst_building(self):
        payload = {"point": self.point_b.pk, "period_start": "2026-01-01", "period_end": "2026-01-31", "quantity": "11"}
        self.assertEqual(self.put("api-consumptionrecord-detail", payload, pk=self.record_b.pk).status_code, 403)
        self.assertEqual(self.client.delete(self.url("api-consumptionrecord-detail", pk=self.record_b.pk)).status_code, 403)
        record_a = ConsumptionRecord.objects.filter(point=self.water_point).first()
        moved = {"point": self.point_b.pk, "period_start": "2026-05-01", "period_end": "2026-05-31", "quantity": "1"}
        self.assertEqual(self.put("api-consumptionrecord-detail", moved, pk=record_a.pk).status_code, 403)
        record_a.refresh_from_db()
        self.assertEqual(record_a.point, self.water_point)

    def test_preload_only_touches_admin_building(self):
        self.building_b.area = 500
        self.building_b.save()
        response = self.post("api-normalizationbase-preload", {"year": 2026})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(set(NormalizationBase.objects.values_list("building", flat=True)), {self.building.pk})

    def test_reviews_alerts_of_admin_building_only(self):
        self.record(self.water_point, 3, "90", self.m3)
        self.record(self.point_b, 2, "10", self.m3)
        self.record(self.point_b, 3, "90", self.m3)
        rule = AlertRule.objects.create(
            organization=self.organization, name="Agua", process="ambiental.consumption",
            trigger=Catalog.objects.get(key=KEY_ALERT_TRIGGER, description=TRIGGER_PERCENT),
            threshold={"percent": "20"}, created_by=self.user, create_task=False,
        )
        evaluate_rule(rule, today=datetime.date(2026, 4, 5))
        alert_a = ConsumptionAlert.objects.get(point=self.water_point)
        alert_b = ConsumptionAlert.objects.get(point=self.point_b)
        note = {"note": "revisada"}
        self.assertEqual(self.post("api-consumptionalert-review", note, pk=alert_a.pk).status_code, 200)
        self.assertEqual(self.post("api-consumptionalert-review", note, pk=alert_b.pk).status_code, 403)


class SingleBuildingRegistryTest(BuildingAccessTestCase):
    """Encargado de registro solo en A: B no existe para él."""

    def setUp(self):
        super().setUp()
        self.registry = self.building_user("registro_a", {self.building: "Encargado de registro ambiental"})
        self.client.force_login(self.registry)

    def test_api_and_selects_hide_the_other_building(self):
        data = self.client.get(self.url("api-consumptionrecord-list")).json()
        self.assertNotIn("Edificio B", {row["building"]["text"] for row in data["data"]})
        buildings = self.client.get(reverse("ambiental_buildings-list"), {"org_pk": self.organization.pk}).json()["results"]
        self.assertEqual([row["text"] for row in buildings], ["Edificio A"])
        points = self.client.get(reverse("ambiental_points-list"), {"org_pk": self.organization.pk}).json()["results"]
        self.assertNotIn(self.point_b.pk, [row["id"] for row in points])
        self.assertEqual(self.client.get(self.url("api-consumptionrecord-detail", pk=self.record_b.pk)).status_code, 404)

    def test_cannot_record_on_hidden_building(self):
        payload = {"point": self.point_b.pk, "period_start": "2026-06-01", "period_end": "2026-06-30", "quantity": "1"}
        response = self.post("api-consumptionrecord-list", payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("point", response.json())

    def test_reports_panel_and_charts_are_scoped(self):
        report = self.make_report("report_consumption_detail")
        report.created_by = self.registry
        report.save()
        reports.report_consumption_detail_html(report)
        self.assertEqual({row[0] for row in report.table_content["dataset"]}, {"Edificio A"})

        response = self.client.get(self.url("ambiental_dashboard"), {"year": 2026})
        self.assertEqual(response.status_code, 200)
        water = next(card for card in response.context["cards"] if card["resource"] == "Agua")
        self.assertEqual(water["quantity"], Decimal("45"))

        chart = reverse("ambientalmonthlyconsumptionchart-detail", kwargs={"pk": self.organization.pk})
        data = self.client.get(chart, {"org_pk": self.organization.pk, "year": 2026}).json()
        series = {dataset["label"]: dataset["data"] for dataset in data["data"]["datasets"]}
        self.assertEqual(series["Agua m³"][0], 30.0)
        self.assertEqual(
            self.client.get(chart, {"org_pk": self.organization.pk, "year": 2026, "building": self.building_b.pk}).status_code,
            404,
        )

    def test_platform_needs_an_organization_role(self):
        admin_a = self.building_user("admin_a", {self.building: "Administrador ambiental"})
        self.client.force_login(admin_a)
        for name in ("platform:systemparameter_list", "platform:notificationsetting_list", "platform:alertrule_list",
                     "platform:api-systemparameter-list", "platform:api-alertrule-list"):
            with self.subTest(route=name):
                response = self.client.get(
                    reverse(name, kwargs={"org_pk": self.organization.pk}), HTTP_X_REQUESTED_WITH="XMLHttpRequest"
                )
                self.assertEqual(response.status_code, 403)


class AlertRecipientsTest(BuildingAccessTestCase):

    def test_rule_roles_only_notify_people_who_see_the_building(self):
        # Los dos tienen el rol de la regla, pero cada uno en un edificio distinto: la
        # alerta de A no puede llegarle a quien solo ve B.
        self.building_user("vigia_a", {self.building: "Analista ambiental"})
        self.building_user("vigia_b", {self.building_b: "Analista ambiental"})
        self.record(self.water_point, 3, "90", self.m3)
        rule = AlertRule.objects.create(
            organization=self.organization, name="Agua", process="ambiental.consumption",
            trigger=Catalog.objects.get(key=KEY_ALERT_TRIGGER, description=TRIGGER_PERCENT),
            threshold={"percent": "20"}, created_by=self.user, create_task=False, notify_responsible=False,
        )
        rule.notify_roles.add(Rol.objects.get(name="Analista ambiental"))
        evaluate_rule(rule, today=datetime.date(2026, 4, 5))
        event = AlertEvent.objects.get()
        self.assertIn("vigia_a", event.recipients)
        self.assertNotIn("vigia_b", event.recipients)


class BuildingAccessScreenTest(BuildingAccessTestCase):

    def roles(self, *names):
        return list(Rol.objects.filter(name__in=names).values_list("pk", flat=True))

    def test_organization_admin_grants_and_updates_without_duplicates(self):
        person = self.building_user("persona", {})
        data = {"user": person.pk, "building": self.building_b.pk, "rol": self.roles("Analista ambiental")}
        response = self.post("api-buildingaccess-list", data)
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["building"]["text"], "Edificio B")
        data["rol"] = self.roles("Encargado de registro ambiental")
        self.assertEqual(self.post("api-buildingaccess-list", data).status_code, 201)
        permission = ProfilePermission.objects.get(profile=person.profile, object_id=self.building_b.pk)
        self.assertEqual(list(permission.rol.values_list("name", flat=True)), ["Encargado de registro ambiental"])
        self.assertTrue(BuildingAccess(person, self.organization).has("ambiental.add_consumptionrecord", self.building_b))
        self.assertFalse(BuildingAccess(person, self.organization).has("ambiental.view_consumptionrecord", self.building))

    def test_non_environmental_roles_are_rejected(self):
        person = self.building_user("persona2", {})
        other_rol = Rol.objects.create(name="Estudiante")
        response = self.post("api-buildingaccess-list", {"user": person.pk, "building": self.building.pk, "rol": [other_rol.pk]})
        self.assertEqual(response.status_code, 400)

    def test_building_admin_only_manages_own_building(self):
        admin_a = self.building_user("admin_a2", {self.building: "Administrador ambiental"})
        person = self.building_user("persona3", {self.building_b: "Analista ambiental"})
        self.client.force_login(admin_a)
        rows = self.client.get(self.url("api-buildingaccess-list")).json()["data"]
        self.assertEqual({row["building"]["text"] for row in rows}, {"Edificio A"})
        response = self.post("api-buildingaccess-list", {
            "user": person.pk, "building": self.building_b.pk, "rol": self.roles("Administrador ambiental"),
        })
        self.assertEqual(response.status_code, 400)
        response = self.post("api-buildingaccess-list", {
            "user": person.pk, "building": self.building.pk, "rol": self.roles("Analista ambiental"),
        })
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(self.client.get(self.url("building_access_list")).status_code, 200)

    def test_removing_user_or_building_cleans_access(self):
        person = self.building_user("persona4", {self.building: "Analista ambiental", self.building_b: "Analista ambiental"})
        building_pps = ProfilePermission.objects.filter(
            profile=person.profile, content_type=ContentType.objects.get_for_model(Buildings)
        )
        self.building_b.delete()
        self.assertEqual(building_pps.count(), 1)

        view = DeleteUserFromContenttypeViewSet()
        view.request = RequestFactory().delete("/")
        view.request.user = self.user
        view.delete_profile_from_organization(person, self.organization)
        self.assertEqual(building_pps.count(), 0)
