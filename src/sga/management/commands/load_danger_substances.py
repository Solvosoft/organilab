from django.core.management import BaseCommand
from sga.models import DangerSubstance, DangerIndication
import csv
import os


class Command(BaseCommand):
    help = 'Import danger substances from CSV file'

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

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                try:
                    cas_code = row.get('cas', '').strip() or None
                    name = row.get('nombre', '').strip()
                    threshold = row.get('umbral_t', '').strip()
                    notes = row.get('notas', '').strip() or None
                    type_match = row.get('tipo_match', '').strip()
                    h_codes_match = row.get('h_codes_match', '').strip()
                    patron_name = row.get('nombre_patron', '').strip()
                    especial_condition = row.get('condiciones_especiales', '').strip()

                    if type_match == 'nombre_patron':
                        type_match = 'patron_name'
                    elif type_match == 'h_categoria':
                        type_match = 'type_match'

                    try:
                        threshold_value = float(threshold) if threshold else 0.0
                    except ValueError:
                        threshold_value = 0.0

                    substance, created = DangerSubstance.objects.update_or_create(
                        cas_code=cas_code,
                        name=name,
                        defaults={
                            'threshold': threshold_value,
                            'notes': notes,
                            'type_match': type_match,
                            'patron_name': patron_name,
                            'especial_condition': especial_condition
                        }
                    )

                    if h_codes_match:
                        h_codes = [code.strip() for code in h_codes_match.split(';')]
                        substance.h_codes_match.clear()

                        for h_code in h_codes:
                            try:
                                danger_indication = DangerIndication.objects.get(
                                    code=h_code)
                                substance.h_codes_match.add(danger_indication)
                            except DangerIndication.DoesNotExist:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'H Code not found: {h_code} for substance: {name}'
                                    )
                                )

                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Created: {name}')
                        )
                    else:
                        updated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Updated: {name}')
                        )

                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error processing row: {row.get("Denominación de la sustancia", "Unknown")} - {str(e)}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nImport completed:\n'
                f'Created: {created_count}\n'
                f'Updated: {updated_count}\n'
                f'Errors: {error_count}'
            )
        )
