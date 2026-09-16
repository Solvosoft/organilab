from datetime import date, datetime, timedelta
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from laboratory.models import (
    Laboratory,
    Object,
    ObjectLogChange,
    PrecursorReport,
    PrecursorReportValues,
    ShelfObject,
)
from laboratory.precursor_reports import current_period, ensure_precursor_report
from laboratory.task_utils import save_object_report_precursor
from laboratory.tasks import create_precursor_reports, verify_precursor_reports
from laboratory.utils_base_unit import get_base_unit
from sga.models import SubstanceCharacteristics


class DecemberPrecursorReportTest(TestCase):
    """El reporte emitido en enero corresponde a diciembre del año anterior.

    La condición estaba invertida (`month_belong == 1 and month == 12`), así que
    el reporte de enero leía los movimientos de diciembre del mismo año.
    """

    fixtures = ["laboratory_data.json"]

    def setUp(self):
        self.lab = Laboratory.objects.get(pk=1)
        self.object = Object.objects.get(pk=1)
        SubstanceCharacteristics.objects.filter(pk=1).update(object_related=self.object)
        shelfobject = ShelfObject.objects.filter(in_where_laboratory=self.lab, object=self.object).first()
        self.unit = get_base_unit(shelfobject.measurement_unit) or shelfobject.measurement_unit
        self.user = User.objects.first()
        self.report = PrecursorReport.objects.create(month=1, year=2026, laboratory=self.lab, month_belong=12)

    def add_log(self, when, amount):
        log = ObjectLogChange.objects.create(
            object=self.object,
            laboratory=self.lab,
            user=self.user,
            diff_value=amount,
            precursor=True,
            measurement_unit=self.unit,
            type_action=0,
        )
        ObjectLogChange.objects.filter(pk=log.pk).update(update_time=timezone.make_aware(when))

    def test_date_range_uses_previous_year(self):
        date_range = str(self.report.get_date_range())
        self.assertIn("2025", date_range)
        self.assertNotIn("2026", date_range)

    def test_values_come_from_december_of_previous_year(self):
        self.add_log(datetime(2025, 12, 15), 5)
        self.add_log(datetime(2026, 12, 15), 100)
        save_object_report_precursor(self.report)
        value = PrecursorReportValues.objects.get(precursor_report=self.report, object=self.object)
        self.assertEqual(value.new_income, 5)


class PrecursorReportConsecutiveTest(TestCase):
    fixtures = ["laboratory_data.json"]

    def test_consecutive_is_numbered_per_laboratory(self):
        lab, other_lab = Laboratory.objects.order_by("pk")[:2]
        first = PrecursorReport.objects.create(month=2, year=2026, laboratory=lab, month_belong=1)
        second = PrecursorReport.objects.create(month=3, year=2026, laboratory=lab, month_belong=2)
        other = PrecursorReport.objects.create(month=3, year=2026, laboratory=other_lab, month_belong=2)
        self.assertEqual((first.consecutive, second.consecutive, other.consecutive), (1, 2, 1))

    def test_update_keeps_consecutive(self):
        report = PrecursorReport.objects.create(month=2, year=2026, laboratory=Laboratory.objects.first(), month_belong=1)
        PrecursorReport.objects.create(month=3, year=2026, laboratory=report.laboratory, month_belong=2)
        report.month_belong = 1
        report.save()
        report.refresh_from_db()
        self.assertEqual(report.consecutive, 1)


class EnsurePrecursorReportsTest(TestCase):
    fixtures = ["laboratory_data.json"]

    def test_current_period_of_january_belongs_to_december(self):
        self.assertEqual(current_period(date(2026, 1, 3)), (1, 2026, 12))
        self.assertEqual(current_period(date(2026, 7, 1)), (7, 2026, 6))

    def test_task_does_not_duplicate_reports(self):
        verify_precursor_reports()
        verify_precursor_reports()
        create_precursor_reports()
        month, year, _ = current_period()
        for lab in Laboratory.objects.all():
            self.assertEqual(PrecursorReport.objects.filter(laboratory=lab, month=month, year=year).count(), 1)

    def test_periods_chain_consecutives(self):
        lab = Laboratory.objects.first()
        ensure_precursor_report(lab, today=date(2026, 1, 31))
        report, created = ensure_precursor_report(lab, today=date(2026, 2, 28))
        self.assertTrue(created)
        self.assertEqual(report.consecutive, 2)
        self.assertFalse(ensure_precursor_report(lab, today=date(2026, 2, 1))[1])


class GeneratePrecursorReportAdminActionTest(TestCase):
    fixtures = ["laboratory_data.json"]

    def test_action_creates_once(self):
        from django.contrib.admin.sites import site
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory

        from laboratory.admin import generate_precursor_report

        modeladmin = site._registry[Laboratory]
        queryset = Laboratory.objects.filter(pk=1)
        for _ in range(2):
            request = RequestFactory().post("/")
            request.user = User.objects.filter(is_superuser=True).first()
            request.session = {}
            request._messages = FallbackStorage(request)
            generate_precursor_report(modeladmin, request, queryset)
        self.assertEqual(PrecursorReport.objects.filter(laboratory_id=1).count(), 1)


class PrecursorReportCommandTest(TestCase):
    fixtures = ["laboratory_data.json"]

    def setUp(self):
        self.lab, self.other_lab = Laboratory.objects.order_by("pk")[:2]
        self.other_report = PrecursorReport.objects.create(month=2, year=2020, laboratory=self.other_lab, month_belong=1)
        PrecursorReport.objects.create(month=2, year=2020, laboratory=self.lab, month_belong=1)
        log = ObjectLogChange.objects.create(
            object=Object.objects.first(),
            laboratory=self.lab,
            user=User.objects.first(),
            measurement_unit=ShelfObject.objects.first().measurement_unit,
        )
        ObjectLogChange.objects.filter(pk=log.pk).update(update_time=timezone.now() - timedelta(days=70))

    def test_requires_confirmation(self):
        with self.assertRaises(CommandError):
            call_command("precursor_report", laboratory=[self.lab.pk], stdout=StringIO())
        self.assertEqual(PrecursorReport.objects.count(), 2)

    def test_rebuilds_only_selected_laboratory(self):
        call_command("precursor_report", laboratory=[self.lab.pk], yes=True, stdout=StringIO())
        self.assertTrue(PrecursorReport.objects.filter(pk=self.other_report.pk).exists())
        reports = PrecursorReport.objects.filter(laboratory=self.lab).order_by("consecutive")
        self.assertGreaterEqual(reports.count(), 2)
        self.assertEqual(list(reports.values_list("consecutive", flat=True)), list(range(1, reports.count() + 1)))
