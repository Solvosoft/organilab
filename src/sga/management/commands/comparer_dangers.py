from django.core.files import File
from django.core.management.base import BaseCommand
from django.conf import settings
import os

from django.db.models import Value, JSONField, F
from django.db.models.functions import JSONObject

from sga.models import DangerIndication, WarningClass, WarningWord
from openpyxl import load_workbook


class Command(BaseCommand):

    def handle(self, *args, **options):
        file = settings.BASE_DIR / "sga/management/commands/SGA_Codigos_H_y_P.xlsx"

        wb = load_workbook(file)
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
