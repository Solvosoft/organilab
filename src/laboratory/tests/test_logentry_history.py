"""El puente organilab_logentry→add_log y el alcance multi-tenant de la
bitácora: las relaciones viven en HistoryRelation y ninguna organización ve
(ni cuenta) los logs de otra."""

from django.contrib.admin.models import ADDITION, LogEntry
from django.test import Client
from django.urls import reverse

from djgentelella.models import HistoryRelation
from laboratory.tests.utils import BaseSetUpAjaxRequest
from laboratory.utils import organilab_logentry


class OrganilabLogentryBridgeTest(BaseSetUpAjaxRequest):

    def test_relobj_instances_become_history_relations(self):
        entry = organilab_logentry(
            self.user1_org1,
            self.lab1_org1,
            ADDITION,
            "laboratory",
            changed_data=["name"],
            change_message="Creado para la prueba",
            relobj=[self.lab1_org1, self.org1],
        )
        self.assertIsInstance(entry, LogEntry)
        self.assertEqual(entry.change_message, "Creado para la prueba")
        rows = HistoryRelation.objects.filter(log_entry=entry)
        self.assertEqual(rows.count(), 2)
        self.assertEqual(
            {row.content_object for row in rows},
            {self.lab1_org1, self.org1},
        )

    def test_relobj_pk_still_resolves_laboratory_with_warning(self):
        with self.assertWarns(DeprecationWarning):
            entry = organilab_logentry(
                self.user1_org1,
                self.lab1_org1,
                ADDITION,
                "laboratory",
                change_message="x",
                relobj=self.lab1_org1.pk,
            )
        row = HistoryRelation.objects.get(log_entry=entry)
        self.assertEqual(row.content_object, self.lab1_org1)

    def test_default_texts_are_unchanged(self):
        entry = organilab_logentry(
            self.user1_org1, self.lab1_org1, ADDITION, "laboratory",
            changed_data=["name"], relobj=self.org1,
        )
        self.assertEqual(entry.object_repr, "Laboratory has been added")
        self.assertEqual(
            entry.change_message, "[{'added': {'fields': ['name']}}]"
        )


class LogEntryScopeTest(BaseSetUpAjaxRequest):
    """El test anti-fuga: dos organizaciones, cada una ve SOLO lo suyo."""

    def setUp(self):
        super().setUp()
        self.url = reverse("laboratory:api-logentry-list")
        self.entry_org1 = organilab_logentry(
            self.user1_org1, self.lab1_org1, ADDITION, "laboratory",
            change_message="org1 log", relobj=[self.org1],
        )
        self.entry_org2 = organilab_logentry(
            self.user2_org2, self.lab2_org2, ADDITION, "laboratory",
            change_message="org2 log", relobj=[self.org2],
        )

    def get_rows(self, client, org):
        response = client.get(self.url, {"org_pk": org.pk})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_each_org_sees_only_its_entries(self):
        payload1 = self.get_rows(self.client1_org1, self.org1)
        ids1 = [row["id"] for row in payload1["data"]]
        self.assertIn(self.entry_org1.pk, ids1)
        self.assertNotIn(self.entry_org2.pk, ids1)

        payload2 = self.get_rows(self.client2_org2, self.org2)
        ids2 = [row["id"] for row in payload2["data"]]
        self.assertIn(self.entry_org2.pk, ids2)
        self.assertNotIn(self.entry_org1.pk, ids2)

    def test_records_total_does_not_leak_between_tenants(self):
        payload = self.get_rows(self.client1_org1, self.org1)
        self.assertEqual(payload["recordsTotal"], len(payload["data"]))
        self.assertLess(payload["recordsTotal"], LogEntry.objects.count())

    def test_a_stranger_org_param_yields_nothing(self):
        # El middleware puede redirigir (302) o el scope responder vacío;
        # lo que NUNCA puede pasar es responder datos.
        response = self.client1_org1.get(self.url, {"org_pk": 999999})
        self.assertIn(response.status_code, (200, 302))
        if response.status_code == 200:
            self.assertEqual(response.json()["recordsTotal"], 0)


class QrBranchScopeTest(BaseSetUpAjaxRequest):
    def test_qr_branch_filters_by_relation_not_by_message(self):
        from laboratory.models import RegisterUserQR
        from auth_and_perms.models import Rol
        from django.contrib.contenttypes.models import ContentType

        qr = RegisterUserQR.objects.create(
            created_by=self.user1_org1,
            url="http://example.com/qr",
            register_user_qr="qr/test.png",
            role=Rol.objects.first(),
            content_type=ContentType.objects.get(
                app_label="laboratory", model="laboratory"
            ),
            object_id=self.lab1_org1.pk,
            organization_creator=self.org1,
            organization_register=self.org1,
            code="Q901",
        )
        wanted = organilab_logentry(
            self.user1_org1, self.user1_org1, ADDITION, "user",
            change_message="Registered via QR", relobj=[self.org1, qr],
        )
        organilab_logentry(
            self.user1_org1, self.user1_org1, ADDITION, "user",
            change_message="Registered via QR", relobj=[self.org1],
        )
        response = self.client1_org1.get(
            reverse("laboratory:api-logentry-list"), {"qr_obj": qr.pk}
        )
        payload = response.json()
        self.assertEqual(payload["recordsTotal"], 1)
        self.assertEqual(payload["data"][0]["id"], wanted.pk)


class PreserveAuditTrailRegressionTest(BaseSetUpAjaxRequest):
    """Borrar un usuario reasigna sus LogEntry al centinela y las
    HistoryRelation (CASCADE del LogEntry) sobreviven con él."""

    def test_relations_survive_user_deletion(self):
        from django.contrib.auth import get_user_model
        from django.test import override_settings

        victim = get_user_model().objects.create_user(
            username="victima", password="x")
        sentinel = get_user_model().objects.create_user(
            username="centinela-test", password="x")
        entry = organilab_logentry(
            victim, self.lab1_org1, ADDITION, "laboratory",
            change_message="antes de borrarme", relobj=[self.org1],
        )
        self.assertEqual(
            HistoryRelation.objects.filter(log_entry=entry).count(), 1)

        from auth_and_perms.utils import preserve_audit_trail_before_delete
        with override_settings(
            DELETED_USER_SENTINEL_USERNAME="centinela-test"
        ):
            preserve_audit_trail_before_delete(victim)
        victim.delete()

        entry.refresh_from_db()
        self.assertEqual(entry.user, sentinel)
        self.assertEqual(
            HistoryRelation.objects.filter(log_entry=entry).count(), 1)
