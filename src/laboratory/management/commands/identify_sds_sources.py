import csv
import os
import re
import subprocess
import sys
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

from laboratory.models import SustanceCharacteristics

SOURCE_KEYWORDS = {
    'Merck': ['merck', 'supelco', 'milliporesigma', 'millipore'],
    'Sigma-Aldrich': ['sigma-aldrich', 'sigma aldrich', 'sigmaaldrich'],
    'Fisher/Thermo': ['fisher', 'thermo scientific', 'thermofisher'],
    'Panreac': ['panreac', 'applichem'],
    'Carlo Erba': ['carlo erba'],
    'JT Baker': ['jt baker', 'j.t. baker', 'jtbaker', 'avantor'],
    'PubChem': ['pubchem'],
    'Honeywell': ['honeywell', 'fluka'],
    'Acros/Alfa Aesar': ['acros', 'alfa aesar'],
    'VWR': ['vwr'],
    'Scharlau': ['scharlau'],
    'CTR': ['ctr scientific', 'ctr grupo'],
    'Oxoid': ['oxoid'],
    'BD/Difco': ['difco', 'becton dickinson', 'bd bbl'],
    'Himedia': ['himedia'],
    'Loba Chemie': ['loba chemie'],
    'Spectrum': ['spectrum chemical'],
    'Karal': ['karal'],
    'Meyer': ['productos quimicos meyer', 'meyer'],
    'Fermont': ['fermont'],
    'Biorad': ['bio-rad', 'biorad'],
    'Riedel-de Haen': ['riedel-de haen', 'riedel'],
    'Mallinckrodt': ['mallinckrodt'],
    'Promega': ['promega'],
    'Invitrogen': ['invitrogen'],
    'Gibco': ['gibco'],
}

from laboratory.utils_pdf import REVISION_DATE_PATTERNS  # noqa: E402


def _extract_text(pdf_path):
    try:
        result = subprocess.run(
            ['pdftotext', '-l', '3', '-q', pdf_path, '-'],
            capture_output=True, text=True, timeout=15
        )
        return result.stdout
    except Exception:
        return ''


def _identify_source(text):
    lower = text.lower()
    for source, keywords in SOURCE_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                return source
    if re.search(r'eq1\.pdf|escuela de qu[ií]mica', lower):
        return 'EQ/UNA'
    return 'Sin identificar'


def _extract_revision_date(text):
    for pattern in REVISION_DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return ''


def _parse_date(date_str):
    if not date_str:
        return None
    for fmt in ('%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%d.%m.%y', '%d/%m/%y'):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def _needs_update(date_str, max_years=5):
    dt = _parse_date(date_str)
    if dt is None:
        return 'desconocido'
    age_days = (datetime.now() - dt).days
    if age_days > max_years * 365:
        return 'si'
    return 'no'


class Command(BaseCommand):
    help = "Identify SDS sources and revision dates, generate CSV report"

    def add_arguments(self, parser):
        parser.add_argument(
            '--output', '-o',
            default='sds_sources_report.csv',
            help='Output CSV file path (default: sds_sources_report.csv)',
        )
        parser.add_argument(
            '--db',
            default='default',
            help='Database alias to query (default: default)',
        )
        parser.add_argument(
            '--max-years',
            type=int,
            default=5,
            help='Max age in years before SDS needs update (default: 5)',
        )
        parser.add_argument(
            '--ids',
            nargs='+',
            type=int,
            help='Specific SustanceCharacteristics PKs to process',
        )

    def handle(self, *args, **options):
        db = options['db']
        output_path = options['output']
        max_years = options['max_years']
        ids = options.get('ids')

        qs = SustanceCharacteristics.objects.using(db).select_related('obj', 'obj__organization').exclude(
            security_sheet=''
        ).exclude(
            security_sheet__isnull=True
        )
        if ids:
            qs = qs.filter(pk__in=ids)

        total = qs.count()
        self.stdout.write(f"Processing {total} substances with security sheets from '{db}'...")

        from collections import Counter
        source_counter = Counter()
        update_counter = Counter()
        rows = []
        errors = 0
        no_file = 0

        for i, sc in enumerate(qs.iterator(), 1):
            name = str(sc.obj) if sc.obj else f"PK={sc.pk}"
            cas = sc.cas_id_number or ''
            org_name = sc.obj.organization.name if sc.obj and sc.obj.organization else ''
            sheet_path = sc.security_sheet.name

            full_path = os.path.join(settings.MEDIA_ROOT, sheet_path)
            if not os.path.exists(full_path):
                no_file += 1
                rows.append({
                    'pk': sc.pk,
                    'cas': cas,
                    'nombre': name,
                    'organizacion': org_name,
                    'fuente': 'archivo_no_encontrado',
                    'fecha_revision': '',
                    'necesita_actualizacion': 'desconocido',
                    'path': sheet_path,
                })
                continue

            text = _extract_text(full_path)
            if not text.strip():
                errors += 1
                rows.append({
                    'pk': sc.pk,
                    'cas': cas,
                    'nombre': name,
                    'organizacion': org_name,
                    'fuente': 'error_lectura',
                    'fecha_revision': '',
                    'necesita_actualizacion': 'desconocido',
                    'path': sheet_path,
                })
                continue

            # Check if filename has eq1 pattern (EQ/UNA source)
            fname = os.path.basename(sheet_path).lower()
            if 'eq1' in fname:
                source = 'EQ/UNA'
            else:
                source = _identify_source(text)

            revision_date = _extract_revision_date(text)
            needs_update = _needs_update(revision_date, max_years)

            source_counter[source] += 1
            update_counter[needs_update] += 1

            rows.append({
                'pk': sc.pk,
                'cas': cas,
                'nombre': name,
                'organizacion': org_name,
                'fuente': source,
                'fecha_revision': revision_date,
                'necesita_actualizacion': needs_update,
                'path': sheet_path,
            })

            if i % 500 == 0:
                self.stdout.write(f"  ...processed {i}/{total}")

        # Write CSV
        fieldnames = ['pk', 'cas', 'nombre', 'organizacion', 'fuente', 'fecha_revision', 'necesita_actualizacion', 'path']
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        self.stdout.write(f"\nReport written to: {output_path}")
        self.stdout.write(f"Total processed: {len(rows)}")
        self.stdout.write(f"Files not found: {no_file}")
        self.stdout.write(f"Read errors: {errors}")

        self.stdout.write("\n--- Sources ---")
        for source, count in source_counter.most_common():
            self.stdout.write(f"  {source}: {count}")

        self.stdout.write("\n--- Needs update ---")
        for status, count in update_counter.most_common():
            self.stdout.write(f"  {status}: {count}")
