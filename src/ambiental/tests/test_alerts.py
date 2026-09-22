import datetime
import json
from decimal import Decimal

from django.urls import reverse
from djgentelella.async_notification.models import EmailNotification, EmailTemplate

from ambiental.alerts import evaluate_rule
from ambiental.models import ConsumptionAlert
from ambiental.tasks import check_consumption_anomalies
from ambiental.tests.test_reports import ReportTestCase
from laboratory.models import Catalog
from pending_tasks.models import PendingTask
from presentation.alerts import (
    ALERT_PROCESSES,
    KEY_ALERT_TRIGGER,
    TRIGGER_ABSOLUTE,
    TRIGGER_MISSING,
    TRIGGER_PERCENT,
)
from presentation.models import AlertEvent, AlertRule, SystemParameter


class ConsumptionAlertTest(ReportTestCase):
    """Agua de enero (30) y febrero (45) en el edificio; se agrega marzo según el caso."""

    def setUp(self):
        super().setUp()
        self.laboratory.responsible = self.user
        self.laboratory.save()
        self.user.email = "responsable@example.com"
        self.user.save()

    def rule(self, trigger, threshold, **kwargs):
        defaults = dict(
            organization=self.organization, name="Consumo de agua", process="ambiental.consumption",
            trigger=Catalog.objects.get(key=KEY_ALERT_TRIGGER, description=trigger),
            threshold=threshold, level=AlertRule.MEDIUM, created_by=self.user,
        )
        defaults.update(kwargs)
        return AlertRule.objects.create(**defaults)

    def test_process_and_email_template_are_registered(self):
        self.assertIn("ambiental.consumption", ALERT_PROCESSES)
        self.assertTrue(EmailTemplate.objects.filter(code="ambiental-consumption-alert").exists())

    def test_percent_over_average_fires_once(self):
        self.record(self.water_point, 3, "52", self.m3)  # promedio 37.5 -> +38.67 %
        rule = self.rule(TRIGGER_PERCENT, {"percent": "20"})
        alerts = evaluate_rule(rule, today=datetime.date(2026, 4, 5))
        self.assertEqual(len(alerts), 1)
        alert = alerts[0]
        self.assertEqual(alert.point, self.water_point)
        self.assertEqual(alert.period, datetime.date(2026, 3, 1))
        self.assertEqual(alert.variation_pct, Decimal("38.67"))
        self.assertEqual(alert.reference_value, Decimal("37.5000"))
        # Avisa al responsable del laboratorio del edificio: correo y tarea.
        notification = EmailNotification.objects.get()
        self.assertEqual(notification.recipients, ["responsable@example.com"])
        self.assertIn("38.67", notification.subject)
        self.assertEqual(PendingTask.objects.count(), 1)
        self.assertEqual(AlertEvent.objects.count(), 1)
        # Correrla de nuevo no duplica.
        self.assertEqual(evaluate_rule(rule, today=datetime.date(2026, 4, 5)), [])
        self.assertEqual(ConsumptionAlert.objects.count(), 1)

    def test_below_threshold_does_not_fire(self):
        self.record(self.water_point, 3, "40", self.m3)
        rule = self.rule(TRIGGER_PERCENT, {"percent": "20"})
        self.assertEqual(evaluate_rule(rule, today=datetime.date(2026, 4, 5)), [])

    def test_window_parameter_limits_history(self):
        self.record(self.water_point, 3, "52", self.m3)
        SystemParameter.objects.create(organization=self.organization, key="ambiental.alert_window_months", raw_value="1")
        rule = self.rule(TRIGGER_PERCENT, {"percent": "20"})
        # Solo febrero (45) entra en la ventana: +15.56 %, bajo el umbral.
        self.assertEqual(evaluate_rule(rule, today=datetime.date(2026, 4, 5)), [])

    def test_absolute_threshold(self):
        rule = self.rule(TRIGGER_ABSOLUTE, {"value": "900"}, create_task=False)
        alerts = evaluate_rule(rule, today=datetime.date(2026, 4, 5))
        self.assertEqual([alert.point for alert in alerts], [self.power_point])

    def test_missing_records(self):
        rule = self.rule(TRIGGER_MISSING, {"months": 1}, create_task=False)
        alerts = evaluate_rule(rule, today=datetime.date(2026, 6, 10))
        self.assertEqual({alert.point for alert in alerts}, {self.water_point, self.power_point})
        self.assertEqual(alerts[0].period, datetime.date(2026, 6, 1))

    def test_task_runs_only_active_rules(self):
        self.record(self.water_point, 3, "52", self.m3)
        self.rule(TRIGGER_PERCENT, {"percent": "20"}, is_active=False)
        self.assertEqual(check_consumption_anomalies(), 0)
        self.rule(TRIGGER_PERCENT, {"percent": "20"}, create_task=False)
        self.assertEqual(check_consumption_anomalies(), 1)
        self.assertEqual(ConsumptionAlert.objects.count(), 1)


class ConsumptionAlertScreenTest(ConsumptionAlertTest):

    def make_alert(self):
        self.record(self.water_point, 3, "52", self.m3)
        rule = self.rule(TRIGGER_PERCENT, {"percent": "20"}, create_task=False)
        return evaluate_rule(rule, today=datetime.date(2026, 4, 5))[0]

    def test_admin_reviews_with_note(self):
        alert = self.make_alert()
        url = reverse("ambiental:api-consumptionalert-review", kwargs={"org_pk": self.organization.pk, "pk": alert.pk})
        self.assertEqual(self.client.post(url, data=json.dumps({"note": ""}), content_type="application/json").status_code, 400)
        response = self.client.post(url, data=json.dumps({"note": "Fuga reparada"}), content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content)
        alert.refresh_from_db()
        self.assertTrue(alert.reviewed)
        self.assertEqual(alert.reviewed_by, self.user)
        rows = self.client.get(
            reverse("ambiental:api-consumptionalert-list", kwargs={"org_pk": self.organization.pk})
        ).json()["data"]
        self.assertEqual(rows[0]["reviewed_note"], "Fuga reparada")
        self.assertFalse(rows[0]["actions"]["review"])

    def test_analista_sees_but_cannot_review(self):
        alert = self.make_alert()
        self.client.force_login(self.make_user("analista_al", self.organization, "Analista ambiental"))
        self.assertEqual(self.client.get(
            reverse("ambiental:consumptionalert_list", kwargs={"org_pk": self.organization.pk})
        ).status_code, 200)
        url = reverse("ambiental:api-consumptionalert-review", kwargs={"org_pk": self.organization.pk, "pk": alert.pk})
        self.assertEqual(self.client.post(url, data=json.dumps({"note": "x"}), content_type="application/json").status_code, 403)

    def test_page_renders_for_each_role(self):
        for rol_name in ("Administrador ambiental", "Encargado de registro ambiental"):
            self.client.force_login(self.make_user("al_" + rol_name.split()[0], self.organization, rol_name))
            with self.subTest(rol=rol_name):
                self.assertEqual(self.client.get(
                    reverse("ambiental:consumptionalert_list", kwargs={"org_pk": self.organization.pk})
                ).status_code, 200)
