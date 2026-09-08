from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from sga.models import WarningWord


class InitChecksTest(TestCase):
    """El comando debe ser idempotente: en un arranque posterior no vuelve a cargar el fixture."""

    def call_init_checks(self, **kwargs):
        out = StringIO()
        call_command("init_checks", stdout=out, **kwargs)
        return out.getvalue()

    def test_loads_fixture_when_sga_components_are_missing(self):
        target = "auth_and_perms.management.commands.init_checks.Command.has_sga_components"
        with patch(target, return_value=False):
            output = self.call_init_checks()

        self.assertIn("Data loaded successfully", output)
        self.assertTrue(WarningWord.objects.exists())

    def test_does_not_reload_fixture_when_components_already_exist(self):
        word = WarningWord.objects.get(pk=1)
        word.name = "editado localmente"
        word.save()

        output = self.call_init_checks()

        self.assertNotIn("Data loaded successfully", output)
        word.refresh_from_db()
        self.assertEqual(word.name, "editado localmente")

    def test_force_fixtures_reloads_and_overwrites(self):
        word = WarningWord.objects.get(pk=1)
        word.name = "editado localmente"
        word.save()

        output = self.call_init_checks(force_fixtures=True)

        self.assertIn("Data loaded successfully", output)
        word.refresh_from_db()
        self.assertNotEqual(word.name, "editado localmente")

    def test_cache_table_name_comes_from_location(self):
        from auth_and_perms.management.commands.init_checks import Command

        caches = {"default": {"BACKEND": "django.core.cache.backends.db.DatabaseCache",
                              "LOCATION": "my_cache_table"}}
        with self.settings(CACHES=caches):
            self.assertEqual(Command().get_cache_table_name(), "my_cache_table")
