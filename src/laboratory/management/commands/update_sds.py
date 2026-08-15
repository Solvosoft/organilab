import time

from django.core.management.base import BaseCommand

from sga.models import SubstanceCharacteristics
from laboratory.sds_sources import get_sources, update_sds_for_substance


class Command(BaseCommand):
    help = "Update outdated SDS (Safety Data Sheets) from external sources"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only report which SDS need updating, without downloading',
        )
        parser.add_argument(
            '--source',
            choices=['merck', 'pubchem', 'all'],
            default='all',
            help='Which source(s) to use (default: all)',
        )
        parser.add_argument(
            '--max-years',
            type=int,
            default=5,
            help='Maximum SDS age in years before it needs updating (default: 5)',
        )
        parser.add_argument(
            '--ids',
            nargs='+',
            type=int,
            help='Specific SubstanceCharacteristics PKs to process',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of substances to process per batch (default: 10)',
        )
        parser.add_argument(
            '--batch-delay',
            type=float,
            default=30.0,
            help='Seconds to wait between batches (default: 30)',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=2.0,
            help='Seconds to wait between downloads for rate limiting (default: 2)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Update even if current SDS is not expired',
        )
        parser.add_argument(
            '--only-missing',
            action='store_true',
            help='Only process substances that have no SDS file at all',
        )
        parser.add_argument(
            '--only-pubchem',
            action='store_true',
            help='Only process substances whose current SDS is from PubChem (synthetic)',
        )
        parser.add_argument(
            '--exclude-source',
            nargs='+',
            choices=['merck', 'pubchem'],
            help='Exclude specific sources from the search (e.g. --exclude-source pubchem)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        source_name = options['source']
        max_years = options['max_years']
        ids = options.get('ids')
        batch_size = options['batch_size']
        batch_delay = options['batch_delay']
        delay = options['delay']
        force = options['force']
        only_missing = options['only_missing']
        only_pubchem = options['only_pubchem']
        exclude_source = options.get('exclude_source')

        source_names = None if source_name == 'all' else [source_name]
        sources = get_sources(source_names)

        if exclude_source:
            sources = [s for s in sources if s.name not in exclude_source]
            if not sources:
                self.stderr.write("No sources left after exclusion. Aborting.")
                return

        qs = SubstanceCharacteristics.objects.select_related('object_related', 'object_related__organization')

        # Only process substances with a CAS number (required for source lookup)
        qs = qs.filter(cas_id_number__isnull=False).exclude(cas_id_number='')

        if only_missing:
            from django.db.models import Q
            qs = qs.filter(Q(security_sheet='') | Q(security_sheet__isnull=True))

        if only_pubchem:
            from sga.models import SDSTraceability
            pubchem_sc_ids = SDSTraceability.objects.filter(
                source='pubchem'
            ).values_list('sga_substance_characteristics_id', flat=True).distinct()
            qs = qs.filter(pk__in=pubchem_sc_ids)

        if ids:
            qs = qs.filter(pk__in=ids)

        all_pks = list(qs.values_list('pk', flat=True))
        total = len(all_pks)
        num_batches = (total + batch_size - 1) // batch_size if total > 0 else 0

        self.stdout.write(
            f"Processing {total} substances in {num_batches} batches of {batch_size} "
            f"(sources: {source_name}, max_years: {max_years}, dry_run: {dry_run})"
        )

        updated = 0
        skipped = 0
        no_source = 0
        errors = 0
        dry_run_count = 0
        processed = 0

        for batch_num in range(num_batches):
            batch_start = batch_num * batch_size
            batch_end = min(batch_start + batch_size, total)
            batch_pks = all_pks[batch_start:batch_end]

            self.stdout.write(
                f"\n--- Batch {batch_num + 1}/{num_batches} "
                f"(substances {batch_start + 1}-{batch_end} of {total}) ---"
            )

            batch_updated = 0
            batch_errors = 0

            batch_qs = SubstanceCharacteristics.objects.select_related(
                'object_related', 'object_related__organization'
            ).filter(pk__in=batch_pks)

            for sc in batch_qs:
                result = update_sds_for_substance(
                    sc, sources=sources, max_years=max_years,
                    dry_run=dry_run, force=force,
                )
                processed += 1
                status = result['status']

                if status == 'updated':
                    updated += 1
                    batch_updated += 1
                    self.stdout.write(
                        f"[OK] {result['name']} (CAS: {result['cas']}) "
                        f"— source: {result['source']}, old_date: {result['old_date']}"
                    )
                    if delay > 0:
                        time.sleep(delay)
                elif status == 'dry_run':
                    dry_run_count += 1
                    self.stdout.write(
                        f"[DRY-RUN] {result['name']} (CAS: {result['cas']}) "
                        f"— needs update, old_date: {result['old_date']}"
                    )
                elif status == 'skipped':
                    skipped += 1
                elif status == 'no_source':
                    no_source += 1
                    self.stderr.write(
                        f"[NO-SOURCE] {result['name']} (CAS: {result['cas']}) "
                        f"— {result.get('error', '')}"
                    )
                elif status == 'error':
                    errors += 1
                    batch_errors += 1
                    self.stderr.write(
                        f"[ERROR] {result['name']} (CAS: {result['cas']}) "
                        f"— {result.get('error', '')}"
                    )

            self.stdout.write(
                f"  Batch {batch_num + 1} done: "
                f"updated={batch_updated}, errors={batch_errors}"
            )

            # Wait between batches (skip delay after the last batch)
            if batch_num < num_batches - 1 and batch_delay > 0:
                self.stdout.write(f"  Waiting {batch_delay}s before next batch...")
                time.sleep(batch_delay)

        prefix = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(
            f"\n{prefix}Summary: processed={processed}, updated={updated}, "
            f"skipped={skipped}, no_source={no_source}, errors={errors}"
        )
        if dry_run:
            self.stdout.write(f"  Substances that need update: {dry_run_count}")
