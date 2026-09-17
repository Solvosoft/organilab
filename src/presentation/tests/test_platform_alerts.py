import json

from django.core import mail
from django.urls import reverse
from djgentelella.async_notification.models import EmailNotification, EmailTemplate
from djgentelella.models import Notification

from auth_and_perms.models import Rol
from laboratory.models import Catalog
from pending_tasks.models import PendingTask
from presentation import alerts
from presentation.models import AlertEvent, AlertRule
from presentation.tests.test_platform_parameters import PlatformTestCase, make_role_user

PROCESS = "platform.test"
FIRED = []


def fake_evaluator(rule, **kwargs):
    FIRED.append(rule.pk)
    alerts.fire_alert(rule, "Algo pasó en %s" % rule.name, link="/x/")


class AlertTestCase(PlatformTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        alerts.register_alert_process(
            PROCESS, label="Proceso de prueba",
            evaluator="presentation.tests.test_platform_alerts.fake_evaluator",
            triggers=(alerts.TRIGGER_PERCENT, alerts.TRIGGER_MISSING),
            permission="presentation.view_alertrule",
            notification_code="platform-test-alert",
        )
        EmailTemplate.objects.create(code="platform-test-alert", subject="Alerta", message="{{ message }}")
        cls.percent = Catalog.objects.get(key=alerts.KEY_ALERT_TRIGGER, description=alerts.TRIGGER_PERCENT)
        cls.absolute = Catalog.objects.get(key=alerts.KEY_ALERT_TRIGGER, description=alerts.TRIGGER_ABSOLUTE)
        cls.receiver = make_role_user("receptor", cls.child, "Analista ambiental")
        cls.receiver.email = "receptor@example.com"
        cls.receiver.save()

    def make_rule(self, **kwargs):
        defaults = dict(
            organization=self.child, name="Regla", process=PROCESS, trigger=self.percent,
            threshold={"percent": "20"}, created_by=self.user,
        )
        defaults.update(kwargs)
        return AlertRule.objects.create(**defaults)


class FireAlertTest(AlertTestCase):

    def test_seeded_triggers(self):
        self.assertEqual(Catalog.objects.filter(key=alerts.KEY_ALERT_TRIGGER).count(), 3)

    def test_fire_notifies_roles_by_email_task_and_bell(self):
        rule = self.make_rule(level=AlertRule.CRITICAL)
        rule.notify_roles.add(Rol.objects.get(name="Analista ambiental"))
        event = alerts.fire_alert(rule, "Consumo alto", link="/detalle/")
        self.assertEqual(event.recipients, ["receptor"])
        notification = EmailNotification.objects.get()
        self.assertEqual(notification.recipients, ["receptor@example.com"])
        self.assertEqual(notification.message, "Consumo alto")
        self.assertEqual(PendingTask.objects.filter(name="Consumo alto").count(), 1)
        self.assertTrue(Notification.objects.filter(user=self.receiver, description="Consumo alto").exists())

    def test_non_critical_does_not_ring_the_bell(self):
        rule = self.make_rule(level=AlertRule.MEDIUM, create_task=False)
        rule.notify_roles.add(Rol.objects.get(name="Analista ambiental"))
        alerts.fire_alert(rule, "Aviso")
        self.assertFalse(Notification.objects.filter(description="Aviso").exists())
        self.assertFalse(PendingTask.objects.exists())

    def test_run_only_active_rules_of_the_process(self):
        FIRED.clear()
        active = self.make_rule()
        self.make_rule(name="Apagada", is_active=False)
        self.assertEqual(alerts.run_alert_rules(PROCESS), 1)
        self.assertEqual(FIRED, [active.pk])
        self.assertEqual(AlertEvent.objects.count(), 1)

    def test_threshold_validation(self):
        self.assertEqual(alerts.validate_threshold(alerts.TRIGGER_MISSING, "2"), {"months": 2})
        with self.assertRaises(ValueError):
            alerts.validate_threshold(alerts.TRIGGER_PERCENT, "-5")


class AlertRuleAPITest(AlertTestCase):

    def url(self, name, **kwargs):
        return reverse("platform:api-alertrule-" + name, kwargs={"org_pk": self.child.pk, **kwargs})

    def payload(self, **kwargs):
        data = {"name": "Agua alta", "process": PROCESS, "trigger": self.percent.pk, "percent": "25",
                "level": "critical", "notification_code": "", "notify_roles": [],
                "notify_responsible": True, "create_task": True, "is_active": True}
        data.update(kwargs)
        return data

    def test_create_builds_threshold(self):
        response = self.client.post(self.url("list"), data=json.dumps(self.payload()), content_type="application/json")
        self.assertEqual(response.status_code, 201, response.content)
        rule = AlertRule.objects.get()
        self.assertEqual(rule.threshold, {"percent": "25"})
        self.assertEqual(rule.organization, self.child)
        row = self.client.get(self.url("list")).json()["data"][0]
        self.assertEqual(row["percent"], "25")
        self.assertEqual(row["process"]["text"], "Proceso de prueba")

    def test_trigger_must_apply_to_process(self):
        response = self.client.post(self.url("list"), data=json.dumps(self.payload(trigger=self.absolute.pk, value="3")),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("trigger", response.json())

    def test_missing_threshold_is_rejected(self):
        response = self.client.post(self.url("list"), data=json.dumps(self.payload(percent="")),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("percent", response.json())

    def test_events_are_listed(self):
        alerts.fire_alert(self.make_rule(create_task=False), "Disparo")
        response = self.client.get(reverse("platform:api-alertevent-list", kwargs={"org_pk": self.child.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"][0]["message"], "Disparo")

    def test_page_renders_for_platform_admins(self):
        for username, rol_name in (("sup_a", "Administrativo superior"), ("amb_a", "Administrador ambiental")):
            self.client.force_login(make_role_user(username, self.child, rol_name))
            with self.subTest(rol=rol_name):
                response = self.client.get(reverse("platform:alertrule_list", kwargs={"org_pk": self.child.pk}))
                self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
