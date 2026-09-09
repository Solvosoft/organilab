# encoding: utf-8
"""Los comandos de siembra tienen que poder correrse dos veces.

El instalador del tenant (`organilab_install`) los encadena, y una persona los
corre a mano al añadir una entrada nueva. Antes, dos de ellos DUPLICABAN sus
datos en la segunda corrida y no fallaba nada: ni `Catalog` ni `Pictogram`
tienen restricción de unicidad, así que no había conflicto que detectar.
"""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from laboratory.models import Catalog
from sga.models import Pictogram


class LoadCommonCatalogsIdempotencyTest(TestCase):

    def run_command(self):
        out = StringIO()
        call_command("load_common_catalogs", stdout=out)
        return out.getvalue()

    def test_running_it_twice_does_not_duplicate_the_catalog(self):
        self.run_command()
        after_first = Catalog.objects.count()
        # La migración 0003_pre_catalog ya siembra estas entradas, así que la
        # primera corrida del comando puede no crear ninguna. Lo que se fija
        # aquí es que la SEGUNDA tampoco añada nada.
        self.assertGreater(after_first, 0)

        self.run_command()

        self.assertEqual(Catalog.objects.count(), after_first)

    def test_it_recreates_only_what_is_missing(self):
        entry = Catalog.objects.filter(key="IDMG").first()
        self.assertIsNotNone(entry)
        key, description = entry.key, entry.description
        entry.delete()
        before = Catalog.objects.count()

        self.run_command()

        self.assertEqual(Catalog.objects.count(), before + 1)
        self.assertTrue(
            Catalog.objects.filter(key=key, description=description).exists()
        )


class UploadPictogramsIdempotencyTest(TestCase):

    def run_command(self, *args):
        out = StringIO()
        call_command("upload_pictograms", *args, stdout=out)
        return out.getvalue()

    def test_running_it_twice_does_not_duplicate_the_pictograms(self):
        self.run_command()
        after_first = Pictogram.objects.count()
        self.assertGreater(after_first, 0)

        output = self.run_command()

        self.assertEqual(Pictogram.objects.count(), after_first)
        self.assertIn("0 created", output)

    def test_no_pictogram_name_is_repeated(self):
        self.run_command()
        self.run_command()

        names = list(Pictogram.objects.values_list("name", flat=True))
        self.assertEqual(len(names), len(set(names)))
