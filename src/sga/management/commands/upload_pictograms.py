import os

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from sga.models import Pictogram

PICTOGRAM_FOLDERS = ("united_nations", "sga")


class Command(BaseCommand):
    help = ("Load the SGA and UN pictograms from the static tree into MEDIA. "
            "Idempotent: a pictogram whose name already exists is left alone.")

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Re-upload the image of pictograms that already exist (overwrites "
                 "whatever is in MEDIA for them)",
        )

    def handle(self, *args, **options):
        # Antes esto era un `Pictogram.objects.create()` a secas, asi que CADA
        # corrida duplicaba los pictogramas y volvia a escribir sus SVG en
        # MEDIA. `Pictogram` no tiene restriccion de unicidad sobre `name`, de
        # modo que el duplicado no fallaba: crecia en silencio.
        created = skipped = replaced = 0

        for folder in PICTOGRAM_FOLDERS:
            path = settings.BASE_DIR / "sga/static/pictograms" / folder
            for filename in sorted(os.listdir(path=path)):
                name = filename.replace(".svg", "")
                existing = Pictogram.objects.filter(name=name).first()

                if existing is not None and not options["replace"]:
                    skipped += 1
                    continue

                with open(path / filename, "r", encoding="utf-8") as open_file:
                    handle = File(open_file)
                    if existing is not None:
                        existing.pictogram.save(filename, handle, save=True)
                        replaced += 1
                    else:
                        Pictogram.objects.create(name=name, pictogram=handle)
                        created += 1

        self.stdout.write(self.style.SUCCESS(
            "Pictograms: %d created, %d replaced, %d already present."
            % (created, replaced, skipped)
        ))
