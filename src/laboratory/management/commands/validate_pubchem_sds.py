import csv
import sys
import time
from collections import Counter

from django.core.management.base import BaseCommand

from laboratory.models import SDSTraceability, SustanceCharacteristics
from laboratory.sds_sources.pubchem import PubChemSource


class Command(BaseCommand):
    help = (
        "Validate PubChem SDS data against stored SustanceCharacteristics. "
        "Generates a CSV report with discrepancies and optionally fixes data."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--output', '-o',
            default='pubchem_validation_report.csv',
            help='Output CSV file path (default: pubchem_validation_report.csv)',
        )
        parser.add_argument(
            '--db',
            default='default',
            help='Database alias to query (default: default)',
        )
        parser.add_argument(
            '--ids',
            nargs='+',
            type=int,
            help='Specific SustanceCharacteristics PKs to process',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.0,
            help='Seconds between PubChem API calls (default: 1.0)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only count matching records, skip API calls',
        )
        parser.add_argument(
            '--verify-cas',
            action='store_true',
            help='Also verify CAS-to-CID mapping via PubChem synonyms',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Batch size for progress reporting (default: 10)',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Apply corrections where PubChem has more complete data',
        )
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Skip confirmation prompt when using --fix',
        )

    def handle(self, *args, **options):
        db = options['db']
        output_path = options['output']
        ids = options.get('ids')
        delay = options['delay']
        dry_run = options['dry_run']
        verify_cas = options['verify_cas']
        batch_size = options['batch_size']
        fix_mode = options['fix']
        no_input = options['no_input']

        qs = (
            SustanceCharacteristics.objects
            .using(db)
            .filter(
                sds_traceability__source='pubchem',
                cas_id_number__isnull=False,
            )
            .exclude(cas_id_number='')
            .select_related('obj', 'obj__organization')
            .distinct()
        )
        if ids:
            qs = qs.filter(pk__in=ids)

        total = qs.count()
        self.stdout.write(f"Found {total} substances with PubChem traceability.")

        if dry_run:
            self.stdout.write("Dry run mode -- skipping API calls.")
            return

        if total == 0:
            self.stdout.write("Nothing to process.")
            return

        source = PubChemSource()
        rows = []
        counters = Counter()
        fixable_rows = []

        for i, sc in enumerate(qs.iterator(), 1):
            name = str(sc.obj) if sc.obj else f"PK={sc.pk}"
            cas = (sc.cas_id_number or '').strip()
            org_name = sc.obj.organization.name if sc.obj and sc.obj.organization else ''

            row = {
                'pk': sc.pk,
                'cas': cas,
                'nombre': name,
                'organizacion': org_name,
                'cid': '',
                'status': '',
                'formula_stored': sc.molecular_formula or '',
                'formula_pubchem': '',
                'formula_match': '',
                'h_codes_stored': '',
                'h_codes_pubchem': '',
                'h_codes_only_stored': '',
                'h_codes_only_pubchem': '',
                'h_codes_match': '',
                'cas_verified': '',
                'cas_in_synonyms': '',
                'other_cas_numbers': '',
                'fixed': '',
            }

            try:
                cid = source._get_cid(cas)
            except Exception as e:
                row['status'] = 'api_error'
                row['fixed'] = ''
                rows.append(row)
                counters['api_error'] += 1
                self.stderr.write(f"  API error for {name} (CAS: {cas}): {e}")
                if i < total:
                    time.sleep(delay)
                continue

            if not cid:
                row['status'] = 'no_cid'
                rows.append(row)
                counters['no_cid'] += 1
                if i < total:
                    time.sleep(delay)
                continue

            row['cid'] = cid

            # Fetch properties and GHS data
            try:
                properties = source._get_properties(cid) or {}
                ghs_data = source._get_ghs_data(cid)
            except Exception as e:
                row['status'] = 'api_error'
                rows.append(row)
                counters['api_error'] += 1
                self.stderr.write(f"  API error for {name} (CID: {cid}): {e}")
                if i < total:
                    time.sleep(delay)
                continue

            # Compare molecular formula
            pubchem_formula = properties.get('MolecularFormula', '')
            row['formula_pubchem'] = pubchem_formula
            stored_formula = (sc.molecular_formula or '').strip()
            row['formula_stored'] = stored_formula

            if stored_formula and pubchem_formula:
                row['formula_match'] = 'yes' if _normalize_formula(stored_formula) == _normalize_formula(pubchem_formula) else 'no'
            elif not stored_formula and pubchem_formula:
                row['formula_match'] = 'stored_empty'
            elif stored_formula and not pubchem_formula:
                row['formula_match'] = 'pubchem_empty'
            else:
                row['formula_match'] = 'both_empty'

            # Compare H-codes
            stored_h_codes = set(sc.h_code.values_list('code', flat=True))
            pubchem_h_codes = set(ghs_data.get('h_codes', [])) if ghs_data else set()
            row['h_codes_stored'] = ';'.join(sorted(stored_h_codes))
            row['h_codes_pubchem'] = ';'.join(sorted(pubchem_h_codes))

            stored_only = stored_h_codes - pubchem_h_codes
            pubchem_only = pubchem_h_codes - stored_h_codes
            row['h_codes_only_stored'] = ';'.join(sorted(stored_only))
            row['h_codes_only_pubchem'] = ';'.join(sorted(pubchem_only))
            row['h_codes_match'] = 'yes' if not stored_only and not pubchem_only else 'no'

            # CAS verification
            if verify_cas:
                try:
                    cas_result = source.verify_cas_for_cid(cid, cas)
                    row['cas_verified'] = 'yes'
                    row['cas_in_synonyms'] = 'yes' if cas_result['cas_found'] else 'no'
                    other_cas = [c for c in cas_result['all_cas_numbers'] if c != cas]
                    row['other_cas_numbers'] = ';'.join(other_cas[:10])
                except Exception:
                    row['cas_verified'] = 'error'

            # Determine overall status
            has_formula_mismatch = row['formula_match'] == 'no'
            has_h_code_mismatch = row['h_codes_match'] == 'no'

            if has_formula_mismatch or has_h_code_mismatch:
                row['status'] = 'mismatch'
                counters['mismatch'] += 1
                if has_formula_mismatch and has_h_code_mismatch:
                    counters['both_mismatch'] += 1
                elif has_formula_mismatch:
                    counters['formula_mismatch_only'] += 1
                else:
                    counters['h_code_mismatch_only'] += 1
            else:
                row['status'] = 'match'
                counters['match'] += 1

            # Track fixable items
            fixes = []
            if pubchem_only and pubchem_h_codes:
                fixes.append('h_codes')
            if row['formula_match'] == 'stored_empty' and pubchem_formula:
                fixes.append('formula')
            if fixes:
                fixable_rows.append((sc.pk, fixes, row, pubchem_formula, pubchem_h_codes))

            if verify_cas and row.get('cas_in_synonyms') == 'no':
                counters['cas_cid_suspect'] += 1

            rows.append(row)

            if i % batch_size == 0:
                self.stdout.write(f"  ...processed {i}/{total}")

            if i < total:
                time.sleep(delay)

        # Apply fixes if requested
        if fix_mode and fixable_rows:
            if not no_input:
                self.stdout.write(
                    f"\nSe encontraron {len(fixable_rows)} sustancias con discrepancias corregibles."
                )
                answer = input("Aplicar correcciones? [s/N] ")
                if answer.strip().lower() not in ('s', 'si', 'y', 'yes'):
                    self.stdout.write("Correcciones canceladas.")
                    fix_mode = False

            if fix_mode:
                self._apply_fixes(fixable_rows, rows, db)

        # Write CSV
        fieldnames = [
            'pk', 'cas', 'nombre', 'organizacion', 'cid', 'status',
            'formula_stored', 'formula_pubchem', 'formula_match',
            'h_codes_stored', 'h_codes_pubchem', 'h_codes_only_stored',
            'h_codes_only_pubchem', 'h_codes_match',
            'cas_verified', 'cas_in_synonyms', 'other_cas_numbers', 'fixed',
        ]
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        self.stdout.write(f"\nReport written to: {output_path}")
        self._print_summary(total, counters, verify_cas)

    def _apply_fixes(self, fixable_rows, rows, db):
        from sga.models import DangerIndication

        available_h_codes = set(
            DangerIndication.objects.using(db).values_list('code', flat=True)
        )
        fixed_count = 0

        for sc_pk, fixes, row, pubchem_formula, pubchem_h_codes in fixable_rows:
            sc = SustanceCharacteristics.objects.using(db).get(pk=sc_pk)
            applied = []

            if 'formula' in fixes and pubchem_formula:
                sc.molecular_formula = pubchem_formula
                sc.save(update_fields=['molecular_formula'])
                applied.append('formula')
                self.stdout.write(f"  Fixed formula for PK={sc_pk}: -> {pubchem_formula}")

            if 'h_codes' in fixes and pubchem_h_codes:
                stored_h_codes = set(sc.h_code.values_list('code', flat=True))
                new_codes = (pubchem_h_codes - stored_h_codes) & available_h_codes
                if new_codes:
                    sc.h_code.add(*new_codes)
                    applied.append(f"h_codes(+{';'.join(sorted(new_codes))})")
                    self.stdout.write(
                        f"  Fixed h_codes for PK={sc_pk}: added {sorted(new_codes)}"
                    )

            if applied:
                row['fixed'] = ','.join(applied)
                fixed_count += 1

        self.stdout.write(f"\nTotal fixed: {fixed_count}")

    def _print_summary(self, total, counters, verify_cas):
        self.stdout.write("\n--- Resumen de Validacion ---")
        self.stdout.write(f"  Total procesados: {total}")
        self.stdout.write(f"  Coincidencia total: {counters.get('match', 0)}")
        self.stdout.write(f"  Formula diferente (solo): {counters.get('formula_mismatch_only', 0)}")
        self.stdout.write(f"  H-codes diferentes (solo): {counters.get('h_code_mismatch_only', 0)}")
        self.stdout.write(f"  Ambos diferentes: {counters.get('both_mismatch', 0)}")
        self.stdout.write(f"  Sin CID: {counters.get('no_cid', 0)}")
        self.stdout.write(f"  Errores API: {counters.get('api_error', 0)}")
        if verify_cas:
            self.stdout.write(f"  CAS-CID sospechoso: {counters.get('cas_cid_suspect', 0)}")


def _normalize_formula(formula):
    """Normalize a molecular formula for comparison."""
    if not formula:
        return ''
    return formula.strip().replace(' ', '').upper()
