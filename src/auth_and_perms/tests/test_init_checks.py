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

    def test_a_redis_cache_has_no_table_to_create(self):
        """LOCATION significa algo distinto en cada backend.

        Con Redis es una URL, y pasársela a createcachetable intentaría crear
        una tabla llamada como la URL. El backend es lo único que los
        distingue: el nombre por sí solo no.
        """
        from auth_and_perms.management.commands.init_checks import Command

        caches = {"default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://acme:secreto@redis:6379/0",
        }}
        with self.settings(CACHES=caches):
            self.assertIsNone(Command().get_cache_table_name())

    def test_does_not_create_a_cache_table_when_the_cache_is_redis(self):
        caches = {"default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://acme:secreto@redis:6379/0",
        }}
        target = "auth_and_perms.management.commands.init_checks.call_command"
        with self.settings(CACHES=caches), patch(target) as call:
            self.call_init_checks()

        called = [args[0] for args, _ in (c for c in call.call_args_list)]
        self.assertNotIn("createcachetable", called)
