from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.db import connection

from sga.models import DangerIndication, PrudenceAdvice, WarningClass, WarningWord

SGA_COMPONENT_MODELS = (WarningClass, WarningWord, PrudenceAdvice, DangerIndication)

DATABASE_CACHE_BACKEND = "django.core.cache.backends.db.DatabaseCache"


class Command(BaseCommand):
    help = "Create the cache table and load the SGA components fixture on a fresh install"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force-fixtures",
            action="store_true",
            help="Reload sga_components.json even if the SGA components already exist "
                 "(overwrites local edits of those records)",
        )

    def get_cache_table_name(self):
        """Table backing the default cache, or None if it is not a DB cache.

        DatabaseCache keeps the table name in LOCATION, not in OPTIONS. But
        LOCATION means something different for every backend: with Redis it is
        a URL (redis://user:pass@host:6379/0), and handing that to
        createcachetable would try to create a table named after the URL. So
        the backend has to be checked first -- the name alone cannot tell them
        apart.
        """
        cache_config = settings.CACHES.get("default", {})
        if cache_config.get("BACKEND") != DATABASE_CACHE_BACKEND:
            return None
        return cache_config.get("LOCATION") or "django_cache"

    def handle(self, *args, **options):
        table_names = connection.introspection.table_names()

        cache_table = self.get_cache_table_name()
        if cache_table is None:
            self.stdout.write(
                "Default cache is not a database cache; nothing to create."
            )
        elif cache_table not in table_names:
            self.stdout.write("Cache table not found. Creating '%s'..." % cache_table)
            call_command("createcachetable")

        if options["force_fixtures"] or not self.has_sga_components():
            self.stdout.write("SGA components not found. Loading data...")
            call_command("loaddata", "sga_components.json")
            self.stdout.write(self.style.SUCCESS("Data loaded successfully"))

    def has_sga_components(self):
        return any(model.objects.exists() for model in SGA_COMPONENT_MODELS)
