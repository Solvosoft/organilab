import json

from django.core.files import File
from django.core.management.base import BaseCommand
from django.conf import settings
import os

from sga.models import Pictogram


class Command(BaseCommand):

    def handle(self, *args, **options):
        for folder in ["united_nations", "sga"]:
            file = settings.BASE_DIR / f"sga/static/pictograms/{folder}"
            for filename in os.listdir(path=file):
                with open(file / filename, 'r', encoding='utf-8') as open_file:
                    f  = File(open_file)
                    filename = filename.replace(".svg","")
                    Pictogram.objects.create(name=filename, pictogram=f)

