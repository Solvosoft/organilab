from django.core.files import File
from django.core.management.base import BaseCommand
from django.conf import settings
from openpyxl.reader.excel import load_workbook

from sga.models import DangerIndication, WarningClass, WarningWord
import csv
import os
import pandas as pd


class Command(BaseCommand):
    help = "Import damger indications from CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            "xlsx_file", type=str, help="Path to the XLSX file to import"
        )

    def handle(self, *args, **options):

        xlsx_file = options["xlsx_file"]

        if not os.path.exists(xlsx_file):
            self.stdout.write(self.style.ERROR(f"File not found: {xlsx_file}"))
            return

        _MAPA_TIPO_SGA = {
            "peligros físicos": "Físico",
            "peligros para la salud": "Salud",
            "peligros para el medio ambiente": "Ambiental",
        }

        wb = load_workbook(xlsx_file)
        ws = wb.worksheets[0]  # hoja activa
        _MAPA_TIPO_SGA = {
            "peligros físicos": "Físico",
            "peligros para la salud": "Salud",
            "peligros para el medio ambiente": "Ambiental",
        }
        i = 0
        for row in ws.iter_rows(min_col=1, max_col=3, values_only=True):
            if len(row[0]) > 0 and i > 0:

                if DangerIndication.objects.filter(code=row[0]).exists():
                    DangerIndication.objects.filter(code=row[0]).update(
                        danger_type=_MAPA_TIPO_SGA.get(row[2].lower())
                    )
                else:
                    warning_words = WarningWord.objects.filter(name="Peligro").first()
                    DangerIndication.objects.create(
                        code=row[0],
                        description=row[1],
                        warning_words=warning_words,
                        danger_type=_MAPA_TIPO_SGA.get(row[2].lower()),
                    )
            i += 1
