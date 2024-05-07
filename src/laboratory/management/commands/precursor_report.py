from datetime import date

from django.contrib.admin.models import CHANGE, ADDITION
from django.core.management.base import BaseCommand
from laboratory.models import ShelfObject, ObjectLogChange, PrecursorReport, \
    PrecursorReportValues, Laboratory
from laboratory.task_utils import save_object_report_precursor, \
    build_precursor_report_from_reports
from laboratory.tasks import create_precursor_reports, add_consecutive


class Command(BaseCommand):

    help = 'Create the report or precursors'

    def get_change_log(self):
        day = date.today()
        ObjectLogChange.objects.filter(subject="Update", diff_value__lte=0).update(type_action=CHANGE)
        ObjectLogChange.objects.filter(subject="Update", diff_value__gte=0).update(type_action=ADDITION)
        for lab in Laboratory.objects.all():

            queryset = ObjectLogChange.objects.filter(laboratory=lab)
            PrecursorReport.objects.filter(laboratory=lab).delete()

            if queryset.exists():
                first_filters = queryset.values("update_time__month", "update_time__year").first()
                month = first_filters['update_time__month']
                x_years = sorted(set(list(queryset.values_list("update_time__year", flat=True))))[0]

                rest_x = day.year-x_years
                year_diiff= (int(day.year)-x_years) if rest_x > 0 else 0

                years =  [x_years]
                while year_diiff>0:
                    x_years += 1
                    years.append(x_years)
                    year_diiff-=1

                years = sorted(list(set(years)))

                for i, year in enumerate(years):

                    months = 12-month
                    i=1

                    if year == day.year:
                        months = day.month-1
                    else:
                        months = 12


                    if months>0:
                        if month == 0:
                            month = 1
                        while months>=month:

                            previos_report = PrecursorReport.objects.filter(laboratory=lab)

                            if previos_report.exists():
                                previos_report = previos_report.last()
                            else:
                                previos_report = None

                            report = PrecursorReport.objects.create(
                                    month=month,
                                    year=year,
                                    laboratory=lab,
                                    consecutive=add_consecutive(lab)
                                )
                            save_object_report_precursor(report)
                            build_precursor_report_from_reports(report, previos_report)
                            i+=1
                            month += 1
                    month = 0


    def create_report(self):
        create_precursor_reports()

    def handle(self, *args, **options):
        self.get_change_log()
