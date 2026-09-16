from datetime import datetime

from django.contrib.auth.models import User
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
from laboratory.task_utils import save_object_report_precursor
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
