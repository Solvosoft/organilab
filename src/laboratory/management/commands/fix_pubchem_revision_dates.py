from django.core.management.base import BaseCommand
from django.db.models import F

from laboratory.models import SDSTraceability


class Command(BaseCommand):
    help = "Fix PubChem SDSTraceability records that have NULL revision_date by setting it to creation_date"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        qs = SDSTraceability.objects.filter(source='pubchem', revision_date__isnull=True)
        count = qs.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No PubChem records with NULL revision_date found."))
            return

        if options['dry_run']:
            self.stdout.write(f"Would update {count} PubChem record(s):")
            for record in qs.select_related('sga_substance_characteristics'):
                self.stdout.write(f"  ID={record.pk}, SC={record.sga_substance_characteristics_id}, created={record.creation_date}")
            return

        updated = qs.update(revision_date=F('creation_date'))
        self.stdout.write(self.style.SUCCESS(f"Updated {updated} PubChem record(s): revision_date = creation_date"))
