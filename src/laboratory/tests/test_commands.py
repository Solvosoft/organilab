from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from laboratory.management.commands.sync_sds_from_old_db import (
    build_sga_map_by_object,
)
from sga.models import SubstanceCharacteristics


class ValidatePubchemSDSCommandTest(TestCase):
    """El comando recorría el modelo obsoleto y fallaba con FieldError.

    `--dry-run` construye el queryset y cuenta sin llamar a la API de PubChem,
    que es justo el punto donde rompía.
    """

    fixtures = ["laboratory_data.json"]

    def test_dry_run_walks_the_sga_queryset(self):
        out = StringIO()
        call_command("validate_pubchem_sds", "--dry-run", stdout=out, stderr=out)
        self.assertIn("Found", out.getvalue())


class SyncSDSFromOldDBMapTest(TestCase):
    """El mapa que traduce las características antiguas a las de SGA.

    El comando escribía la FK que eliminó `laboratory.0212`. La traducción va por
    el `Object` compartido, igual que en `laboratory.0211`; se prueba aparte
    porque el comando sale antes si no puede conectar con la base antigua.
    """

    fixtures = ["laboratory_data.json"]

    def test_map_indexes_characteristics_by_object(self):
        mapping = build_sga_map_by_object()
        self.assertTrue(mapping, "la fixture no trae características con objeto")

        for object_id, sga_pk in mapping.items():
            self.assertEqual(
                SubstanceCharacteristics.objects.get(pk=sga_pk).object_related_id,
                object_id,
            )

    def test_map_ignores_characteristics_without_object(self):
        orphan = SubstanceCharacteristics.objects.create(object_related=None)
        self.assertNotIn(orphan.pk, build_sga_map_by_object().values())


class UpdateSDSForSubstanceTest(TestCase):
    """La descarga automática leía `sc.obj`, que solo existe en el modelo viejo.

    `dry_run` recorre el mismo arranque —resolver nombre y CAS— sin llegar a
    salir a la red, que es donde saltaba el AttributeError.
    """

    fixtures = ["laboratory_data.json"]

    def test_dry_run_resolves_the_name_from_the_related_object(self):
        from laboratory.sds_sources import update_sds_for_substance

        characteristics = SubstanceCharacteristics.objects.exclude(
            object_related=None
        ).first()

        result = update_sds_for_substance(characteristics, sources=[], dry_run=True)

        self.assertEqual(result["status"], "dry_run")
        self.assertEqual(result["name"], str(characteristics.object_related))
