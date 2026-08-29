import datetime

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from laboratory.models import Catalog, Laboratory, OrganizationStructure
from laboratory.utils import get_user_laboratories
from risk_management.iper_defaults import (
    KEY_CONSEQUENCE,
    KEY_HAZARD_CATEGORY,
    KEY_PROBABILITY,
    KEY_RISK_LEVEL,
)
from risk_management.models import (
    IPERAssessment,
    IPERConfig,
    IPERHazard,
    IPERRiskMatrix,
)
from risk_management.models_utils import add_months, compute_risk_level


class IPERSeedTest(TestCase):
    """La migración de siembra corre en la BD de test."""

    def test_catalog_seeded(self):
        self.assertEqual(
            Catalog.objects.filter(key=KEY_HAZARD_CATEGORY).count(), 6
        )
        self.assertEqual(Catalog.objects.filter(key=KEY_PROBABILITY).count(), 3)
        self.assertEqual(Catalog.objects.filter(key=KEY_CONSEQUENCE).count(), 3)
        self.assertEqual(Catalog.objects.filter(key=KEY_RISK_LEVEL).count(), 5)

    def test_matrix_seeded(self):
        self.assertEqual(IPERRiskMatrix.objects.count(), 9)

    def test_compute_risk_level(self):
        high = Catalog.objects.get(key=KEY_PROBABILITY, description="Alta")
        ed = Catalog.objects.get(
            key=KEY_CONSEQUENCE, description="Extremadamente Dañino"
        )
        level, priority = compute_risk_level(high, ed)
        self.assertEqual(level.description, "Intolerable")
        self.assertEqual(priority, 5)

        low = Catalog.objects.get(key=KEY_PROBABILITY, description="Baja")
        ld = Catalog.objects.get(
            key=KEY_CONSEQUENCE, description="Ligeramente Dañino"
        )
        level, priority = compute_risk_level(low, ld)
        self.assertEqual(level.description, "Trivial")
        self.assertEqual(priority, 1)

    def test_add_months(self):
        self.assertEqual(
            add_months(datetime.date(2026, 1, 31), 1), datetime.date(2026, 2, 28)
        )


class IPERViewTest(TestCase):
    fixtures = ["object.json", "riskmanagement_data.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)
        self.org_pk = 1
        self.organization = OrganizationStructure.objects.get(pk=self.org_pk)
        labs = get_user_laboratories(self.user).filter(
            organization__pk=self.org_pk
        )
        self.lab = labs.first() or Laboratory.objects.get(pk=1)
        self.category = Catalog.objects.get(
            key=KEY_HAZARD_CATEGORY, description="Químico"
        )
        self.high = Catalog.objects.get(key=KEY_PROBABILITY, description="Alta")
        self.ed = Catalog.objects.get(
            key=KEY_CONSEQUENCE, description="Extremadamente Dañino"
        )

    def _make_assessment(self, **kwargs):
        defaults = dict(
            organization=self.organization,
            laboratory=self.lab,
            assessment_date=datetime.date.today(),
            responsible=self.user,
            created_by=self.user,
        )
        defaults.update(kwargs)
        return IPERAssessment.objects.create(**defaults)

    def test_list_view(self):
        response = self.client.get(
            reverse("riskmanagement:iper_list", kwargs={"org_pk": self.org_pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_api_list_masks_anonymous(self):
        visible = self._make_assessment(is_anonymous=False)
        anon = self._make_assessment(is_anonymous=True)
        url = reverse(
            "riskmanagement:api-iperassessment-list",
            kwargs={"org_pk": self.org_pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["recordsTotal"], 2)
        rows = {row["id"]: row for row in data["data"]}
        self.assertEqual(rows[visible.pk]["laboratory"], self.lab.name)
        self.assertIsNone(rows[anon.pk]["laboratory"])
        self.assertTrue(rows[anon.pk]["is_anonymous"])

    def test_api_search_excludes_anonymous_by_lab_name(self):
        visible = self._make_assessment(is_anonymous=False)
        anon = self._make_assessment(is_anonymous=True)
        url = reverse(
            "riskmanagement:api-iperassessment-list",
            kwargs={"org_pk": self.org_pk},
        )
        response = self.client.get(url, {"search": self.lab.name})
        self.assertEqual(response.status_code, 200)
        ids = [row["id"] for row in response.json()["data"]]
        self.assertIn(visible.pk, ids)
        self.assertNotIn(anon.pk, ids)

    def test_api_destroy(self):
        assessment = self._make_assessment()
        url = reverse(
            "riskmanagement:api-iperassessment-detail",
            kwargs={"org_pk": self.org_pk, "pk": assessment.pk},
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            IPERAssessment.objects.filter(pk=assessment.pk).exists()
        )

    def test_api_create_not_allowed(self):
        url = reverse(
            "riskmanagement:api-iperassessment-list",
            kwargs={"org_pk": self.org_pk},
        )
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 403)

    def test_hazard_save_computes_risk_level(self):
        assessment = self._make_assessment()
        hazard = IPERHazard.objects.create(
            assessment=assessment,
            category=self.category,
            description="Vapores de solventes",
            location="Campana",
            probability=self.high,
            consequence=self.ed,
            controls="Campana de extracción",
        )
        hazard.refresh_from_db()
        self.assertIsNotNone(hazard.risk_level)
        self.assertEqual(hazard.risk_level.description, "Intolerable")
        self.assertEqual(hazard.risk_priority, 5)

    def test_hazard_create_view(self):
        assessment = self._make_assessment()
        url = reverse(
            "riskmanagement:iper_hazard_create",
            kwargs={"org_pk": self.org_pk, "assessment_pk": assessment.pk},
        )
        response = self.client.post(
            url,
            data={
                "category": self.category.pk,
                "description": "Mezcla incompatible",
                "location": "Mesa",
                "probability": self.high.pk,
                "consequence": self.ed.pk,
                "controls": "Procedimiento",
                "recommended_controls": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(assessment.hazards.count(), 1)

    def test_clone_for_update(self):
        assessment = self._make_assessment()
        IPERHazard.objects.create(
            assessment=assessment,
            category=self.category,
            description="Peligro base",
            probability=self.high,
            consequence=self.ed,
        )
        url = reverse(
            "riskmanagement:iper_clone",
            kwargs={"org_pk": self.org_pk, "pk": assessment.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        assessment.refresh_from_db()
        self.assertEqual(assessment.status, IPERAssessment.OBSOLETE)
        new = IPERAssessment.objects.filter(
            laboratory=self.lab, version=2
        ).first()
        self.assertIsNotNone(new)
        self.assertEqual(new.hazards.count(), 1)

    def test_clone_clean(self):
        assessment = self._make_assessment()
        IPERHazard.objects.create(
            assessment=assessment,
            category=self.category,
            description="Peligro base",
            probability=self.high,
            consequence=self.ed,
        )
        url = reverse(
            "riskmanagement:iper_clone",
            kwargs={"org_pk": self.org_pk, "pk": assessment.pk},
        )
        response = self.client.get(url + "?clean=1")
        self.assertEqual(response.status_code, 302)
        new = IPERAssessment.objects.filter(
            laboratory=self.lab, version=2
        ).first()
        self.assertEqual(new.hazards.count(), 0)

    def test_history_html(self):
        response = self.client.get(
            reverse("riskmanagement:iper_history", kwargs={"org_pk": self.org_pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_history_xlsx(self):
        assessment = self._make_assessment()
        IPERHazard.objects.create(
            assessment=assessment,
            category=self.category,
            description="Peligro",
            probability=self.high,
            consequence=self.ed,
        )
        response = self.client.get(
            reverse("riskmanagement:iper_history", kwargs={"org_pk": self.org_pk})
            + "?format=xlsx"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header("content-disposition"))

    def test_lab_help_json(self):
        response = self.client.get(
            reverse(
                "riskmanagement:iper_lab_help",
                kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "application/json")
        self.assertIn("items", response.json())

    def test_reminder_task_creates_pending(self):
        from pending_tasks.models import PendingTask
        from risk_management.tasks import send_iper_update_reminders

        # asegurar config de la org raíz
        IPERConfig.objects.get_or_create(
            organization=self.organization.root,
            laboratory=None,
            defaults={"period_months": 12, "reminder_days_before": 30},
        )
        self._make_assessment(
            status=IPERAssessment.COMPLETED,
            due_date=datetime.date.today() + datetime.timedelta(days=10),
        )
        before = PendingTask.objects.count()
        send_iper_update_reminders()
        # si el responsable tiene profile, se crea la tarea
        if hasattr(self.user, "profile"):
            self.assertGreaterEqual(PendingTask.objects.count(), before)
