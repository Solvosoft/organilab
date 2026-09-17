import json

from django.urls import reverse
from djgentelella.async_notification.models import EmailNotification, EmailTemplate
from djgentelella.async_notification.registry import register_context

from presentation.models import NotificationSetting
from presentation.notifications import send_process_email
from presentation.tests.test_platform_parameters import PlatformTestCase

CODE = "platform-test-process"


class SendProcessEmailTest(PlatformTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        register_context(code=CODE, subject="Hola {{ name }}", models={}, extra_variables={"name": "Nombre"})
        EmailTemplate.objects.create(code=CODE, subject="Hola {{ name }}", message="Mensaje para {{ name }}")

    def test_uses_global_template_by_default(self):
        notification = send_process_email(self.child, CODE, {"name": "Ana"}, "ana@example.com")
        self.assertEqual(notification.subject, "Hola Ana")
        self.assertEqual(notification.recipients, ["ana@example.com"])

    def test_inherited_setting_can_turn_it_off(self):
        NotificationSetting.objects.create(organization=self.root, code=CODE, is_active=False)
        self.assertIsNone(send_process_email(self.child, CODE, {"name": "Ana"}, ["ana@example.com"]))
        self.assertEqual(EmailNotification.objects.count(), 0)

    def test_own_override_wins_over_ancestor(self):
        NotificationSetting.objects.create(organization=self.root, code=CODE, is_active=False)
        NotificationSetting.objects.create(
            organization=self.child, code=CODE, override_subject="Aviso para {{ name }}"
        )
        notification = send_process_email(self.child, CODE, {"name": "Ana"}, ["ana@example.com"])
        self.assertEqual(notification.subject, "Aviso para Ana")
        self.assertEqual(notification.message, "Mensaje para Ana")

    def test_missing_template_does_not_raise(self):
        self.assertIsNone(send_process_email(self.child, "sin-plantilla", {}, ["ana@example.com"]))

    def test_api_update_and_restore(self):
        url = reverse("platform:api-notificationsetting-detail", kwargs={"org_pk": self.child.pk, "pk": CODE})
        response = self.client.put(
            url, data=json.dumps({"is_active": False, "override_subject": "", "override_message": ""}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertFalse(response.json()["is_active"])
        rows = self.client.get(
            reverse("platform:api-notificationsetting-list", kwargs={"org_pk": self.child.pk})
        ).json()["data"]
        self.assertIn(CODE, [row["code"] for row in rows])
        restore = reverse("platform:api-notificationsetting-restore", kwargs={"org_pk": self.child.pk, "pk": CODE})
        self.assertEqual(self.client.post(restore).status_code, 200)
        self.assertFalse(NotificationSetting.objects.exists())

    def test_page_renders(self):
        response = self.client.get(reverse("platform:notificationsetting_list", kwargs={"org_pk": self.child.pk}))
        self.assertEqual(response.status_code, 200)
