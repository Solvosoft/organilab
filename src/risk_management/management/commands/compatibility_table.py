import csv
import io

import ezodf

from django.core.management import BaseCommand

from risk_management.compatibility_utils import (
    get_h_code_compatibility,
    get_zone_substances,
    collect_h_codes,
    build_compatibility_matrix,
    get_incompatibility_alerts,
    add_ods_styles,
    build_zone_ods_sheet,
    H_CODE_TO_CLASS,
)
from risk_management.models import Buildings, RiskZone


class Command(BaseCommand):
    help = 'Genera tabla de compatibilidad química por códigos H en edificios/zonas de riesgo'

    def add_arguments(self, parser):
        parser.add_argument('--building', type=int, help='ID del edificio específico')
        parser.add_argument('--organization', type=int, help='ID de la organización')
        parser.add_argument(
            '--output', type=str, default='console',
            choices=['console', 'csv', 'ods'], help='Formato de salida'
        )
        parser.add_argument(
            '--filename', type=str, default='compatibility_table.ods',
            help='Nombre del archivo de salida (solo para formato ods)'
        )

    def handle(self, *args, **options):
        building_id = options['building']
        organization_id = options['organization']
        output_format = options['output']
        filename = options['filename']

        buildings_qs = Buildings.objects.all()
        if building_id:
            buildings_qs = buildings_qs.filter(pk=building_id)
        if organization_id:
            buildings_qs = buildings_qs.filter(organization_id=organization_id)

        if not buildings_qs.exists():
            self.stdout.write(self.style.WARNING('No se encontraron edificios con los filtros proporcionados.'))
            return

        if output_format == 'ods':
            doc = ezodf.newdoc(doctype='ods', filename=filename)
            add_ods_styles(doc)
            if len(doc.sheets) > 0:
                del doc.sheets[0]
            for building in buildings_qs:
                zones = RiskZone.objects.filter(buildings=building)
                for zone in zones:
                    build_zone_ods_sheet(building, zone, doc)
            if len(doc.sheets) == 0:
                self.stdout.write(self.style.WARNING('No se generaron hojas (sin datos de compatibilidad).'))
                return
            doc.save()
            self.stdout.write(self.style.SUCCESS('Archivo ODS generado: %s' % filename))
            return

        for building in buildings_qs:
            if output_format == 'console':
                self.print_building_console(building)
            else:
                self.print_building_csv(building)

    def print_building_console(self, building):
        """Print compatibility table for a building in console format."""
        self.stdout.write('=' * 64)
        self.stdout.write('EDIFICIO: %s (ID: %d)' % (building.name, building.pk))
        self.stdout.write('=' * 64)
        self.stdout.write('')

        zones = RiskZone.objects.filter(buildings=building)
        if not zones.exists():
            self.stdout.write(self.style.WARNING(
                '  No se encontraron zonas de riesgo para este edificio.'
            ))
            self.stdout.write('')
            return

        for zone in zones:
            self.stdout.write('--- Zona de Riesgo: %s (Prioridad: %d) ---' % (
                zone.name, zone.priority
            ))

            lab_substances = get_zone_substances(zone)
            if not lab_substances:
                self.stdout.write('  No se encontraron sustancias reactivas con códigos H en esta zona.')
                self.stdout.write('')
                continue

            for lab, substances in lab_substances.items():
                self.stdout.write('  Lab: %s' % lab.name)
                substance_strs = []
                for name, h_codes in substances:
                    substance_strs.append('%s (%s)' % (name, ', '.join(h_codes)))
                self.stdout.write('    Sustancias: %s' % ', '.join(substance_strs))

            all_h_codes = collect_h_codes(lab_substances)
            self.stdout.write('')
            self.stdout.write('  Códigos H presentes: %s' % ', '.join(all_h_codes))
            self.stdout.write('')

            if len(all_h_codes) < 2:
                self.stdout.write('  (Se necesitan al menos 2 códigos H distintos para generar la tabla)')
                self.stdout.write('')
                continue

            matrix = build_compatibility_matrix(all_h_codes)

            self.stdout.write('  TABLA DE COMPATIBILIDAD:')
            col_width = 7
            header = ' ' * 8
            for code in all_h_codes:
                header += code.rjust(col_width)
            self.stdout.write('  ' + header)

            for row_code in all_h_codes:
                row = row_code.ljust(8)
                for col_code in all_h_codes:
                    val = matrix[row_code][col_code]
                    if val == '-':
                        cell = '-'
                    else:
                        cell = '[%s]' % val
                    row += cell.center(col_width)
                self.stdout.write('  ' + row)

            self.stdout.write('')
            self.stdout.write('  Leyenda: [V]=Verde/Compatible  [A]=Amarillo/Precaución  [R]=Rojo/Incompatible')

            alerts = get_incompatibility_alerts(all_h_codes)
            if alerts:
                self.stdout.write('')
                self.stdout.write('  ALERTAS DE INCOMPATIBILIDAD:')
                for alert in alerts:
                    self.stdout.write(
                        '  [ROJO] %s (%s) <-> %s (%s)' % (
                            alert['code_a'], alert['desc_a'],
                            alert['code_b'], alert['desc_b'],
                        )
                    )
                    self.stdout.write('         → %s' % alert['reason'])
            else:
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS(
                    '  No se encontraron incompatibilidades (ROJO) en esta zona.'
                ))

            self.stdout.write('')

    def print_building_csv(self, building):
        """Print compatibility table for a building in CSV format."""
        zones = RiskZone.objects.filter(buildings=building)

        for zone in zones:
            lab_substances = get_zone_substances(zone)
            if not lab_substances:
                continue

            all_h_codes = collect_h_codes(lab_substances)
            if len(all_h_codes) < 2:
                continue

            matrix = build_compatibility_matrix(all_h_codes)

            output = io.StringIO()
            writer = csv.writer(output)

            writer.writerow(['Edificio', building.name, 'ID', building.pk])
            writer.writerow(['Zona de Riesgo', zone.name, 'Prioridad', zone.priority])
            writer.writerow([])

            writer.writerow([''] + all_h_codes)
            for row_code in all_h_codes:
                row = [row_code]
                for col_code in all_h_codes:
                    row.append(matrix[row_code][col_code])
                writer.writerow(row)

            writer.writerow([])

            alerts = get_incompatibility_alerts(all_h_codes)
            if alerts:
                writer.writerow(['ALERTAS DE INCOMPATIBILIDAD'])
                writer.writerow(['Nivel', 'Código A', 'Descripción A', 'Código B', 'Descripción B', 'Razón'])
                for alert in alerts:
                    writer.writerow([
                        'ROJO',
                        alert['code_a'], alert['desc_a'],
                        alert['code_b'], alert['desc_b'],
                        alert['reason'],
                    ])

            writer.writerow([])
            self.stdout.write(output.getvalue())
