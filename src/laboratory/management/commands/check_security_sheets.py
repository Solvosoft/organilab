import json
import os
from collections import defaultdict

import pdfplumber
from django.core.management.base import BaseCommand
from django.conf import settings
from laboratory.models import SDSTraceability


class Command(BaseCommand):
    help = "Verifica la existencia de archivos security_sheet en la carpeta media"

    def contains_pubchem_source(self, file_path):
        """Verifica si el archivo PDF contiene 'Fuente: PubChem'."""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    try:
                        text = page.extract_text() or ""
                    except Exception:
                        text = ""
                    if "Fuente: PubChem" in text:
                        return True
            return False
        except Exception:
            return False

    def save_pubchem_files(self, file_list, output_path):
        """Guarda la lista de archivos con fuente PubChem en un archivo txt."""
        with open(output_path, "w", encoding="utf-8") as f:
            for item in file_list:
                f.write(f"{item}\n")

    def save_file_index_json(self, file_index):
        """Guarda el índice de rutas de archivos en formato JSON."""
        output_path = os.path.join(os.path.dirname(__file__), "file_index.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dict(file_index), f, ensure_ascii=False, indent=2)

    def handle(self, *args, **options):
        sustances = SDSTraceability.objects.exclude(
            sustance_characteristics__security_sheet__isnull=True
        ).exclude(sustance_characteristics__security_sheet="")

        total = sustances.count()

        self.stdout.write(f"Total de registros con security_sheet: {total}\n")
        self.stdout.write("-" * 80)

        base_path = os.path.join(settings.MEDIA_ROOT, "sustancecharacteristics")

        # Indexar archivos excluyendo los que tienen PubChem
        self.stdout.write("Indexando archivos...")
        file_index = defaultdict(list)
        for root, dirs, files in os.walk(base_path):
            for file_name in files:
                full_path = os.path.join(root, file_name)
                if not self.contains_pubchem_source(full_path):
                    file_index[file_name].append(full_path)
        self.stdout.write(
            f"Archivos indexados (sin PubChem): {sum(len(v) for v in file_index.values())}"
        )

        self.save_file_index_json(file_index)
        self.stdout.write("Índice guardado en file_index.json")

        listado = []
        for sc in sustances:
            file_name = os.path.basename(
                sc.sustance_characteristics.security_sheet.name
            )

            # Verificar si el archivo actual tiene PubChem
            has_pubchem = self.contains_pubchem_source(
                sc.sustance_characteristics.security_sheet.path
            )

            if has_pubchem:
                listado.append(sc.sustance_characteristics.cas_id_number)
                print(sc.sustance_characteristics.cas_id_number)
            elif not has_pubchem:
                continue

            # Buscar reemplazo en el índice
            for full_path in file_index.get(file_name, []):
                file_path = os.path.relpath(full_path, settings.MEDIA_ROOT)
                ss = sc.sustance_characteristics
                ss.security_sheet = file_path
                ss.save()

        print(f"Total con PubChem: {len(listado)}")
