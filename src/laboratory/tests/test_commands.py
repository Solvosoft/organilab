import os
import tempfile
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from laboratory.management.commands.sync_sds_from_old_db import (
    build_sga_map_by_object,
)
from laboratory.models import Laboratory, Object, ShelfObject
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


class CheckInWhereLaboratoryCommandTest(TestCase):
    """`in_where_laboratory` debe coincidir con el laboratorio del estante.

    Sin `--fix` el comando solo reporta y revierte la transacción; con `--fix`
    corrige el valor a partir de la cadena estante → mueble → sala → laboratorio.
    """

    fixtures = ["laboratory_data.json"]

    def setUp(self):
        self.shelfobject = ShelfObject.objects.select_related("shelf__furniture__labroom").get(pk=1)
        self.chain_lab_id = self.shelfobject.shelf.furniture.labroom.laboratory_id
        self.other_lab = Laboratory.objects.exclude(pk=self.chain_lab_id).first()
        ShelfObject.objects.filter(pk=1).update(in_where_laboratory=self.other_lab)

    def run_command(self, *args):
        out = StringIO()
        call_command("check_in_where_laboratory", *args, stdout=out)
        return out.getvalue()

    def test_reports_mismatch_without_changing_data(self):
        output = self.run_command("--summary-only")
        self.assertIn("Laboratory mismatches: 1", output)
        self.shelfobject.refresh_from_db()
        self.assertEqual(self.shelfobject.in_where_laboratory_id, self.other_lab.pk)

    def test_fix_restores_chain_laboratory(self):
        output = self.run_command("--summary-only", "--fix")
        self.assertNotIn("Fixed: 0", output)
        self.shelfobject.refresh_from_db()
        self.assertEqual(self.shelfobject.in_where_laboratory_id, self.chain_lab_id)


class CheckShelfObjectChainCommandTest(TestCase):
    fixtures = ["laboratory_data.json"]

    def test_summary_counts_every_object(self):
        out = StringIO()
        call_command("check_shelfobject_chain", "--summary-only", stdout=out)
        self.assertIn(f"Total reviewed: {Object.objects.count()}", out.getvalue())


class CheckObjectsFromFileCommandTest(TestCase):
    fixtures = ["laboratory_data.json"]

    def test_missing_file_raises(self):
        with self.assertRaises(CommandError):
            call_command("check_objects_from_file", "--file", "/nonexistent/ids.txt", stdout=StringIO())

    def test_reports_ids_not_found(self):
        existing = ShelfObject.objects.order_by("pk").first().object_id
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as handler:
            handler.write(f"{existing}\n999999\nabc\n")
        self.addCleanup(os.remove, handler.name)
        out = StringIO()
        call_command("check_objects_from_file", "--file", handler.name, stdout=out)
        self.assertIn("999999", out.getvalue())
