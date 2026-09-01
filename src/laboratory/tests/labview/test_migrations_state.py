# encoding: utf-8
"""El estado de las migraciones, como prueba y no como paso manual.

``makemigrations --check`` es un criterio de aceptación del roadmap, y un
criterio que sólo vive en una lista se degrada sin que nadie lo note.  Aquí se
comprueba lo mismo desde la suite: que el labview no añade esquema (por diseño
lleva una única migración de datos) y que no queda ningún cambio pendiente.
"""

from django.apps import apps
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.questioner import NonInteractiveMigrationQuestioner
from django.db.migrations.state import ProjectState
from django.test import TestCase


def pending_changes():
    """``{app_label: [migraciones que faltarían]}``."""
    loader = MigrationLoader(None, ignore_no_migrations=True)
    autodetector = MigrationAutodetector(
        loader.project_state(),
        ProjectState.from_apps(apps),
        NonInteractiveMigrationQuestioner(specified_apps=set(), dry_run=True),
    )
    return autodetector.changes(
        graph=loader.graph, trim_to_apps=None, convert_apps=None, migration_name=None
    )


class MigrationStateTest(TestCase):

    def test_nothing_is_pending(self):
        changes = pending_changes()
        self.assertEqual(
            dict(changes),
            {},
            "faltan migraciones por generar: %s" % sorted(changes),
        )

    def test_the_labview_adds_no_schema_migration(self):
        """La etapa lleva una migración de datos y ninguna de esquema."""
        loader = MigrationLoader(None, ignore_no_migrations=True)
        migration = loader.disk_migrations[
            ("laboratory", "0223_normalize_dataconfig")
        ]
        self.assertEqual(
            [type(operation).__name__ for operation in migration.operations],
            ["RunPython"],
        )

    def test_the_data_migration_is_reversible_as_a_noop_and_elidable(self):
        """Normalizar el formato no tiene vuelta atrás que valga la pena.

        El formato antiguo se sigue leyendo, así que revertir es no hacer nada;
        y una vez convergido el dato, la migración puede desaparecer al
        aplastar el historial.
        """
        from django.db import migrations

        loader = MigrationLoader(None, ignore_no_migrations=True)
        operation = loader.disk_migrations[
            ("laboratory", "0223_normalize_dataconfig")
        ].operations[0]
        self.assertIs(operation.reverse_code, migrations.RunPython.noop)
        self.assertTrue(operation.elidable)
