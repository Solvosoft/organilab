
from django.core.management import BaseCommand
from sga.models import DangerSubstanceCategory, DangerIndication
from laboratory.models import Catalog
import csv
import os


class Command(BaseCommand):
    help = 'Import danger substance categories from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file to import'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']

        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file}'))
            return

        created_count = 0
        updated_count = 0
        error_count = 0

        category_mapping = {
            'Salud': 'health',
            'Físico': 'physical',
            'Ambiental': 'environmental'
        }

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                try:
                    h_code_str = row.get('h_code', '').strip()
                    category_str = row.get('categoria', '').strip()
                    section = row.get('seccion', '').strip() or None
                    process_condition_str = row.get('condicion_proceso', '').strip()
                    note = row.get('notas', '').strip() or None
                    threshold = row.get('umbral_t', '').strip()

                    try:
                        h_code = DangerIndication.objects.get(code=h_code_str)
                    except DangerIndication.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(f'H Code not found: {h_code_str}')
                        )
                        error_count += 1
                        continue

                    category = category_mapping.get(category_str)
                    if not category:
                        self.stdout.write(
                            self.style.WARNING(f'Unknown category: {category_str}, skipping')
                        )
                        error_count += 1
                        continue

                    try:
                        threshold_value = float(threshold) if threshold else 0.0
                    except ValueError:
                        threshold_value = 0.0

                    process_condition = None
                    if process_condition_str:
                        process_condition, _ = Catalog.objects.get_or_create(
                            key='process_condition',
                            description=process_condition_str,
                            defaults={'description': process_condition_str}
                        )

                    substance_category, created = DangerSubstanceCategory.objects.update_or_create(
                        h_code=h_code,
                        category=category,
                        section=section,
                        defaults={
                            'process_condition': process_condition,
                            'note': note,
                            'threshold': threshold_value,
                        }
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Created: {h_code_str} - {category_str}')
                        )
                    else:
                        updated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Updated: {h_code_str} - {category_str}')
                        )

                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error processing row: {row.get("Código H", "Unknown")} - {str(e)}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nImport completed:\n'
                f'Created: {created_count}\n'
                f'Updated: {updated_count}\n'
                f'Errors: {error_count}'
            )
        )
