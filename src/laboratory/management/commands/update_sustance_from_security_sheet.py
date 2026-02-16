import os

from django.conf import settings
from django.core.management.base import BaseCommand

from laboratory.models import Catalog, SustanceCharacteristics
from laboratory.utils_pdf import extract_catalog_fields, extract_msds_data
from sga.models import DangerIndication

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

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        only_empty = options['only_empty']
        ids = options.get('ids')

        # Load catalog data for catalog field extraction
        catalog_data = {}
        for key in _CATALOG_KEYS:
            catalog_data[key] = list(
                Catalog.objects.filter(key=key).order_by('pk').values_list('pk', 'description')
            )

        qs = SustanceCharacteristics.objects.exclude(
            security_sheet=''
        ).exclude(
            security_sheet__isnull=True
        ).select_related('obj')

        if ids:
            qs = qs.filter(pk__in=ids)

        total = qs.count()
        updated = 0
        skipped = 0
        errors = 0

        for sc in qs.iterator():
            name = str(sc.obj) if sc.obj else f"PK={sc.pk}"
            file_path = os.path.join(settings.MEDIA_ROOT, sc.security_sheet.name)

            if not os.path.exists(file_path):
                self.stderr.write(f"[SKIP] {name} (PK={sc.pk}): file not found at {file_path}")
                skipped += 1
                continue

            data = extract_msds_data(file_path)
            if data is None:
                self.stderr.write(f"[ERROR] {name} (PK={sc.pk}): failed to extract data from PDF")
                errors += 1
                continue

            # Extract catalog fields from the raw PDF text
            pdf_text = data.pop('_text', '')
            catalog_fields = extract_catalog_fields(pdf_text, catalog_data) if pdf_text else {}

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

            # Handle catalog FK fields
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

            # Handle catalog M2M fields
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
            if h_codes:
                h_code_objects = list(
                    DangerIndication.objects.filter(code__in=h_codes)
                )
                if h_code_objects:
                    current_codes = set(sc.h_code.values_list('code', flat=True))
                    new_codes = {di.code for di in h_code_objects}
                    codes_to_add = new_codes - current_codes
                    if only_empty:
                        if current_codes:
                            codes_to_add = set()
                    if codes_to_add:
                        changes.append(f"h_code=+[{','.join(sorted(codes_to_add))}]")

            if not changes:
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(f"[DRY-RUN] {name} (PK={sc.pk}): {', '.join(changes)}")
            else:
                sc.save()
                # Save M2M catalog fields
                for field_name, pks_to_add in m2m_adds.items():
                    getattr(sc, field_name).add(*pks_to_add)
                # Save h_code M2M
                if h_code_objects and any(c.startswith('h_code=') for c in changes):
                    codes_to_add_objs = [
                        di for di in h_code_objects
                        if di.code in (new_codes - current_codes)
                    ]
                    if codes_to_add_objs:
                        sc.h_code.add(*codes_to_add_objs)
                self.stdout.write(f"[OK] {name} (PK={sc.pk}): {', '.join(changes)}")

            updated += 1

            warnings = []
            if not data.get('cas_id_number'):
                warnings.append('CAS number')
            if not data.get('molecular_formula'):
                warnings.append('molecular formula')
            if warnings:
                self.stderr.write(
                    f"[WARN] {name} (PK={sc.pk}): could not extract {', '.join(warnings)}"
                )

        self.stdout.write("")
        prefix = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(
            f"{prefix}Processed: {total}, Updated: {updated}, "
            f"Skipped: {skipped}, Errors: {errors}"
        )
