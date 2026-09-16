import calendar

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Min
from django.utils.timezone import now

from laboratory.models import Laboratory, PrecursorReport
from laboratory.precursor_reports import ensure_precursor_report


class Command(BaseCommand):
    help = (
        "Rebuild the precursor reports of the given laboratories from their object log changes. "
        "The existing reports of those laboratories are deleted first."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--laboratory",
            action="append",
            type=int,
            required=True,
            help="Laboratory pk to rebuild (repeatable)",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Confirm the deletion of the existing reports of the selected laboratories",
        )

    def handle(self, *args, **options):
        labs = (
            Laboratory.objects.filter(pk__in=options["laboratory"])
            .annotate(
                changelog_count=Count("objectlogchange"),
                update_time_min=Min("objectlogchange__update_time"),
            )
            .filter(changelog_count__gt=0)
        )
        existing = PrecursorReport.objects.filter(laboratory__in=labs)
        if not options["yes"]:
            raise CommandError(
                "%d existing reports in %d laboratories would be deleted; run again with --yes to confirm"
                % (existing.count(), labs.count())
            )
        existing.delete()

        actual_date = now()
        for lab in labs:
            current_time = lab.update_time_min
            created = 0
            while current_time < actual_date:
                current_time = current_time + relativedelta(months=+1)
                current_time = current_time.replace(day=calendar.monthrange(current_time.year, current_time.month)[1])
                created += ensure_precursor_report(lab, today=current_time.date())[1]
            self.stdout.write(f"Laboratory {lab.pk}: {created} reports created")
