import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import django
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections

from laboratory.models import Catalog, SustanceCharacteristics
from laboratory.utils_pdf import extract_catalog_fields, extract_msds_data

# Catalog keys used for catalog field extraction
_CATALOG_KEYS = ['IARC', 'IDMG', 'white_organ', 'ue_code', 'nfpa', 'storage_class', 'Precursor']

# FK fields: catalog result key -> model field suffix (_id)
_FK_CATALOG_FIELDS = {
    'iarc': ('iarc_id', lambda v: v is None),
    'imdg': ('imdg_id', lambda v: v is None),
    'precursor_type': ('precursor_type_id', lambda v: v is None),
}

# M2M fields: catalog result key -> model field name
_M2M_CATALOG_FIELDS = ['white_organ', 'ue_code', 'nfpa', 'storage_class']


def _resolve_pdf_path(sc):
    """Resolve the PDF path for a SustanceCharacteristics in MEDIA_ROOT."""
    if not sc.security_sheet or not sc.security_sheet.name:
        return None

    local_path = os.path.join(settings.MEDIA_ROOT, sc.security_sheet.name)
    if os.path.exists(local_path):
        return local_path

    return None


def _process_one(sc_pk, catalog_data, dry_run, only_empty, update_sds=False, sds_max_years=5,
                 sds_delay=2, sources=None):
    """Process a single SustanceCharacteristics. Returns a result dict.

    Runs in a worker process — closes inherited DB connections so each
    process opens its own fresh connection.
    """
    django.setup()
    connections.close_all()

    from laboratory.models import SustanceCharacteristics
    from sga.models import DangerIndication  # noqa: F811

    result = {
        'pk': sc_pk,
        'status': None,  # 'updated', 'skipped', 'error'
        'stdout': [],
        'stderr': [],
    }
    try:
        sc = SustanceCharacteristics.objects.select_related('obj').get(pk=sc_pk)
    except SustanceCharacteristics.DoesNotExist:
        result['status'] = 'error'
        result['stderr'].append(f"[ERROR] PK={sc_pk}: not found")
        return result

    name = str(sc.obj) if sc.obj else f"PK={sc.pk}"
    file_path = os.path.join(settings.MEDIA_ROOT, sc.security_sheet.name) if sc.security_sheet else ''
    file_exists = sc.security_sheet and file_path and os.path.exists(file_path)

    if update_sds:
        cas = (sc.cas_id_number or '').strip()
        if cas:
            from laboratory.sds_sources import check_needs_update, get_sources, update_sds_for_substance

            needs_download = not file_exists
            if file_exists and not needs_download:
                needs_update, _ = check_needs_update(file_path, sds_max_years)
                needs_download = needs_update

            if needs_download:
                # Build sources inside worker if not provided (not serializable across processes)
                if sources is None:
                    sources = get_sources()

                existing_pdf_path = _resolve_pdf_path(sc)

                sds_result = update_sds_for_substance(
                    sc, sources=sources, max_years=sds_max_years, force=True,
                    existing_pdf_path=existing_pdf_path
                )
                if sds_result['status'] == 'updated':
                    result['stdout'].append(
                        f"[SDS] {name} (PK={sc.pk}): downloaded from {sds_result['source']}"
                    )
                    sc.refresh_from_db()
                    file_path = os.path.join(settings.MEDIA_ROOT, sc.security_sheet.name)
                    file_exists = True
                elif sds_result['status'] == 'error':
                    result['stderr'].append(
                        f"[SDS-WARN] {name} (PK={sc.pk}): {sds_result.get('error', 'unknown error')}"
                    )
                elif sds_result['status'] == 'no_source':
                    result['stderr'].append(
                        f"[SDS-WARN] {name} (PK={sc.pk}): no source could provide SDS"
                    )

                if sds_delay > 0:
                    time.sleep(sds_delay)

    if not file_exists:
        result['status'] = 'skipped'
        result['stderr'].append(f"[SKIP] {name} (PK={sc.pk}): file not found at {file_path}")
        return result

    data = extract_msds_data(file_path)
    if data is None:
        result['status'] = 'error'
        result['stderr'].append(f"[ERROR] {name} (PK={sc.pk}): failed to extract data from PDF")
        return result

    pdf_text = data.pop('_text', '')

    # Create traceability record for existing PDFs if none exists
    try:
        from laboratory.models import SDSTraceability
        from laboratory.management.commands.identify_sds_sources import _identify_source, _extract_revision_date, _parse_date
        from laboratory.sds_sources import SOURCE_NAME_TO_KEY

        if not SDSTraceability.objects.filter(sustance_characteristics=sc).exists():
            source_name = _identify_source(pdf_text) if pdf_text else 'Sin identificar'
            source_key = SOURCE_NAME_TO_KEY.get(source_name, 'unknown')
            rev_date_str = _extract_revision_date(pdf_text) if pdf_text else ''
            rev_date = _parse_date(rev_date_str)
            SDSTraceability.objects.create(
                sustance_characteristics=sc,
                source=source_key,
                revision_date=rev_date,
            )
    except Exception as e:
        result['stderr'].append(f"[WARN] {name} (PK={sc.pk}): could not create traceability record: {e}")
    lang = data.get('_lang', 'es')
    catalog_fields = extract_catalog_fields(pdf_text, catalog_data, lang) if pdf_text else {}

    changes = []
    simple_fields = {
        'cas_id_number': ('cas_id_number', lambda v: not v),
        'molecular_formula': ('molecular_formula', lambda v: not v),
        'density': ('density', lambda v: v == 0 or v is None),
        'bioaccumulable': ('bioaccumulable', lambda v: v is None),
        'seveso_list': ('seveso_list', lambda v: v is False),
        'is_precursor': ('is_precursor', lambda v: v is False),
    }

    for data_key, (model_field, is_empty_fn) in simple_fields.items():
        value = data.get(data_key)
        if value is None:
            continue
        current = getattr(sc, model_field)
        if only_empty and not is_empty_fn(current):
            continue
        if current != value:
            changes.append(f"{model_field}={value}")
            if not dry_run:
                setattr(sc, model_field, value)

    for cat_key, (model_field, is_empty_fn) in _FK_CATALOG_FIELDS.items():
        value = catalog_fields.get(cat_key)
        if value is None:
            continue
        current = getattr(sc, model_field)
        if only_empty and not is_empty_fn(current):
            continue
        if current != value:
            changes.append(f"{cat_key}={value}")
            if not dry_run:
                setattr(sc, model_field, value)

    m2m_adds = {}
    for field_name in _M2M_CATALOG_FIELDS:
        pks = catalog_fields.get(field_name, [])
        if not pks:
            continue
        current_pks = set(getattr(sc, field_name).values_list('pk', flat=True))
        pks_to_add = set(pks) - current_pks
        if only_empty and current_pks:
            pks_to_add = set()
        if pks_to_add:
            m2m_adds[field_name] = sorted(pks_to_add)
            changes.append(f"{field_name}=+{sorted(pks_to_add)}")

    h_codes = data.get('h_codes', [])
    h_code_objects = []
    codes_to_add = set()
    if h_codes:
        h_code_objects = list(DangerIndication.objects.filter(code__in=h_codes))
        if h_code_objects:
            current_codes = set(sc.h_code.values_list('code', flat=True))
            new_codes = {di.code for di in h_code_objects}
            codes_to_add = new_codes - current_codes
            if only_empty and current_codes:
                codes_to_add = set()
            if codes_to_add:
                changes.append(f"h_code=+[{','.join(sorted(codes_to_add))}]")

    if not changes:
        result['status'] = 'skipped'
    else:
        if dry_run:
            result['stdout'].append(f"[DRY-RUN] {name} (PK={sc.pk}): {', '.join(changes)}")
        else:
            sc.save()
            for field_name, pks_to_add in m2m_adds.items():
                getattr(sc, field_name).add(*pks_to_add)
            if codes_to_add and h_code_objects:
                codes_to_add_objs = [di for di in h_code_objects if di.code in codes_to_add]
                if codes_to_add_objs:
                    sc.h_code.add(*codes_to_add_objs)
            result['stdout'].append(f"[OK] {name} (PK={sc.pk}): {', '.join(changes)}")
        result['status'] = 'updated'

    warnings = []
    if not data.get('cas_id_number'):
        warnings.append('CAS number')
    if not data.get('molecular_formula'):
        warnings.append('molecular formula')
    if warnings:
        result['stderr'].append(
            f"[WARN] {name} (PK={sc.pk}): could not extract {', '.join(warnings)}"
        )

    return result


class Command(BaseCommand):
    help = "Extract data from security_sheet PDFs and update SustanceCharacteristics fields"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be updated without saving',
        )
        parser.add_argument(
            '--only-empty',
            action='store_true',
            help='Only update fields that are currently empty/null/default',
        )
        parser.add_argument(
            '--ids',
            nargs='+',
            type=int,
            help='Specific SustanceCharacteristics PKs to process',
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=1,
            help='Number of parallel processes for PDF processing (default: 1)',
        )
        parser.add_argument(
            '--skip-sds-update',
            action='store_true',
            help='Do not attempt to download SDS from external sources (use only existing PDFs)',
        )
        parser.add_argument(
            '--sds-max-years',
            type=int,
            default=5,
            help='Maximum age in years before considering an SDS outdated (default: 5)',
        )
        parser.add_argument(
            '--sds-delay',
            type=float,
            default=2,
            help='Delay in seconds between SDS downloads to avoid rate limiting (default: 2)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        only_empty = options['only_empty']
        ids = options.get('ids')
        workers = options['workers']
        update_sds = not options['skip_sds_update']
        sds_max_years = options['sds_max_years']
        sds_delay = options['sds_delay']

        catalog_data = {}
        for key in _CATALOG_KEYS:
            catalog_data[key] = list(
                Catalog.objects.filter(key=key).order_by('pk').values_list('pk', 'description')
            )

        qs = SustanceCharacteristics.objects.exclude(
            security_sheet=''
        ).exclude(
            security_sheet__isnull=True
        )

        if ids:
            qs = qs.filter(pk__in=ids)

        sc_pks = list(qs.values_list('pk', flat=True))
        total = len(sc_pks)
        updated = 0
        skipped = 0
        errors = 0

        if workers > 1:
            with ProcessPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(
                        _process_one, pk, catalog_data, dry_run, only_empty,
                        update_sds, sds_max_years, sds_delay
                    ): pk
                    for pk in sc_pks
                }
                for future in as_completed(futures):
                    try:
                        res = future.result()
                    except Exception as exc:
                        pk = futures[future]
                        self.stderr.write(f"[ERROR] PK={pk}: {exc}")
                        errors += 1
                        continue
                    for line in res['stdout']:
                        self.stdout.write(line)
                    for line in res['stderr']:
                        self.stderr.write(line)
                    if res['status'] == 'updated':
                        updated += 1
                    elif res['status'] == 'error':
                        errors += 1
                    else:
                        skipped += 1
        else:
            for pk in sc_pks:
                res = _process_one(
                    pk, catalog_data, dry_run, only_empty,
                    update_sds, sds_max_years, sds_delay
                )
                for line in res['stdout']:
                    self.stdout.write(line)
                for line in res['stderr']:
                    self.stderr.write(line)
                if res['status'] == 'updated':
                    updated += 1
                elif res['status'] == 'error':
                    errors += 1
                else:
                    skipped += 1

        self.stdout.write("")
        prefix = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(
            f"{prefix}Processed: {total}, Updated: {updated}, "
            f"Skipped: {skipped}, Errors: {errors}"
        )
