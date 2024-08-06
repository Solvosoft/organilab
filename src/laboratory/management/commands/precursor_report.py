from dateutil.relativedelta import relativedelta
from django.contrib.admin.models import CHANGE, ADDITION
from django.core.management.base import BaseCommand
from django.db.models import Count, Min
from django.utils.timezone import now

from laboratory.models import ObjectLogChange, PrecursorReport, \
    Laboratory
from laboratory.task_utils import save_object_report_precursor, \
    build_precursor_report_from_reports
from laboratory.tasks import add_consecutive


class Command(BaseCommand):

    help = 'Create the report or precursors'

    def get_change_log(self):
        PrecursorReport.objects.all().delete()

        actual_date = now() - relativedelta(months=1)
        ObjectLogChange.objects.filter(subject="Update", diff_value__lte=0).update(type_action=CHANGE)
        ObjectLogChange.objects.filter(subject="Update", diff_value__gte=0).update(type_action=ADDITION)
        labs = Laboratory.objects.all().annotate(changelog_count=Count('objectlogchange'),
                                           update_time_min=Min('objectlogchange__update_time'),
                                           ).filter(
            changelog_count__gt=0)

        for lab in labs:
            current_time=lab.update_time_min
            previos_report=None
            while current_time<actual_date:

                report = PrecursorReport.objects.create(
                    month=current_time.month,
                    year=current_time.year,
                    laboratory=lab,
                    consecutive=add_consecutive(lab)
                )
                save_object_report_precursor(report)
                build_precursor_report_from_reports(report, previos_report)
                previos_report=report
                current_time=current_time+relativedelta(months=+1)
                print("Running on %s for %d of %d" % (
                    str(lab),
                    current_time.year,
                    current_time.month
                ))

    def handle(self, *args, **options):
        self.get_change_log()
