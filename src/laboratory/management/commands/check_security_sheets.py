import os
from django.core.management.base import BaseCommand
from django.conf import settings
from laboratory.models import SustanceCharacteristics


class Command(BaseCommand):
    help = "Verifica la existencia de archivos security_sheet en la carpeta media"

    def add_arguments(self, parser):
        parser.add_argument(
            "--missing-only",
            action="store_true",
            help="Mostrar solo los archivos faltantes",
        )
        parser.add_argument(
            "--existing-only",
            action="store_true",
            help="Mostrar solo los archivos existentes",
        )

    def handle(self, *args, **options):
        missing_only = options["missing_only"]
        existing_only = options["existing_only"]

        sustances = SustanceCharacteristics.objects.exclude(
            security_sheet__isnull=True
        ).exclude(security_sheet="")

        total = sustances.count()
        existing = 0
        missing = 0

        self.stdout.write(f"Total de registros con security_sheet: {total}\n")
        self.stdout.write("-" * 80)

        base_path = os.path.join(settings.MEDIA_ROOT, "sustancecharacteristics")

        for sc in sustances:
            file_name = os.path.basename(sc.security_sheet.name)
            exists = False
            file_path = None

            for root, dirs, files in os.walk(base_path):
                if file_name in files:
                    full_path = os.path.join(root, file_name)
                    file_path = os.path.relpath(full_path, settings.MEDIA_ROOT)
                    exists = True
                    sc.security_sheet = file_path
                    sc.save()
                    break

            if exists:
                existing += 1
                if not missing_only:
                    self.stdout.write(
                        self.style.SUCCESS(f"[OK] ID:{sc.pk} - {file_name}")
                    )
            else:
                missing += 1
                if not existing_only:
                    self.stdout.write(
                        self.style.ERROR(f"[FALTA] ID:{sc.pk} - {file_name}")
                    )

        self.stdout.write("-" * 80)
        self.stdout.write(f"Existentes: {existing}")
        self.stdout.write(f"Faltantes: {missing}")
