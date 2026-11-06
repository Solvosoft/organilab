"""Detalle, edición y borrado en las APIs de plataforma: lo que no ejercita el listado."""
import json

from django.urls import reverse
from djgentelella.async_notification.registry import register_context

from presentation.models import AlertRule, NotificationSetting
from presentation.tests import test_platform_alerts as alert_base
from presentation.tests import test_platform_notifications as notification_base


class NotificationSettingDetailTest(alert_base.PlatformTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        register_context(code=notification_base.CODE, subject="Hola", models={}, extra_variables={})

    def url(self, name, pk=notification_base.CODE):
        return reverse("platform:api-notificationsetting-" + name, kwargs={"org_pk": self.child.pk, "pk": pk})

    def test_detalle_muestra_el_valor_heredado(self):
        NotificationSetting.objects.create(organization=self.root, code=notification_base.CODE,
                                           override_subject="Asunto raíz")
        for name in ("detail", "get-values-for-update"):
            with self.subTest(name=name):
                row = self.client.get(self.url(name)).json()
                self.assertEqual(row["override_subject"], "Asunto raíz")
                self.assertIn(str(self.root), row["origin_display"])
                self.assertFalse(row["actions"]["restore"])

    def test_proceso_desconocido_es_404(self):
        self.assertEqual(self.client.get(self.url("detail", pk="no-existe")).status_code, 404)


class SystemParameterDetailTest(alert_base.PlatformTestCase):
    key = "ambiental.alert_window_months"

    def test_detalle_y_valores_para_editar(self):
        for name in ("detail", "get-values-for-update"):
            with self.subTest(name=name):
                url = reverse("platform:api-systemparameter-" + name, kwargs={"org_pk": self.child.pk, "pk": self.key})
                row = self.client.get(url).json()
                self.assertEqual((row["key"], row["value"]), (self.key, "12"))


class AlertRuleDetailTest(alert_base.AlertTestCase):

    def url(self, name, **kwargs):
        return reverse("platform:api-alertrule-" + name, kwargs={"org_pk": self.child.pk, **kwargs})

    def test_correo_desconocido_es_rechazado(self):
        payload = {"name": "Agua", "process": alert_base.PROCESS, "trigger": self.percent.pk, "percent": "25",
                   "level": "critical", "notification_code": "correo-inexistente", "notify_roles": []}
        response = self.client.post(self.url("list"), data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("notification_code", response.json())

    def test_borrar_una_regla(self):
        rule = self.make_rule()
        response = self.client.delete(self.url("detail", pk=rule.pk))
        self.assertIn(response.status_code, (200, 204), response.content)
        self.assertFalse(AlertRule.objects.filter(pk=rule.pk).exists())
