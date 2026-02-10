from dateutil.relativedelta import relativedelta
from django.contrib.admin.models import CHANGE, ADDITION
from django.core.management.base import BaseCommand
from django.db.models import Count, Min
from django.utils.timezone import now

from laboratory.models import ObjectLogChange, PrecursorReport, Laboratory
from laboratory.task_utils import (
    save_object_report_precursor,
    build_precursor_report_from_reports,
)
from laboratory.tasks import add_consecutive
import calendar


class Command(BaseCommand):
    help = "Create the report or precursors"

    def get_change_log(self):
        PrecursorReport.objects.all().delete()

        actual_date = now()
        # ObjectLogChange.objects.filter(subject="Update", diff_value__lte=0).update(type_action=CHANGE)
        # ObjectLogChange.objects.filter(subject="Update", diff_value__gte=0).update(type_action=ADDITION)
        labs = (
            Laboratory.objects.filter(pk=55)
            .annotate(
                changelog_count=Count("objectlogchange"),
                update_time_min=Min("objectlogchange__update_time"),
            )
            .filter(changelog_count__gt=0)
        )

        for lab in labs:
            current_time = lab.update_time_min
            previos_report = None
            while current_time < actual_date:
                current_time = current_time + relativedelta(months=+1)
                current_time = current_time.replace(
                    day=calendar.monthrange(current_time.year, current_time.month)[1]
                )
                month_belong = current_time.month - 1
                if current_time.month == 1:
                    month_belong = 12

                report = PrecursorReport.objects.create(
                    month=current_time.month,
                    year=current_time.year,
                    laboratory=lab,
                    consecutive=add_consecutive(lab),
                    month_belong=month_belong,
                )
                save_object_report_precursor(report)
                build_precursor_report_from_reports(report, previos_report)
                previos_report = report

    def handle(self, *args, **options):
        self.get_change_log()
