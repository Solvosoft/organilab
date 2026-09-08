from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.db import connection

from sga.models import DangerIndication, PrudenceAdvice, WarningClass, WarningWord

SGA_COMPONENT_MODELS = (WarningClass, WarningWord, PrudenceAdvice, DangerIndication)


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
        """DatabaseCache keeps the table name in LOCATION, not in OPTIONS."""
        cache_config = settings.CACHES.get("default", {})
        return cache_config.get("LOCATION") or "django_cache"

    def handle(self, *args, **options):
        table_names = connection.introspection.table_names()

        cache_table = self.get_cache_table_name()
        if cache_table not in table_names:
            self.stdout.write("Cache table not found. Creating '%s'..." % cache_table)
            call_command("createcachetable")

        if options["force_fixtures"] or not self.has_sga_components():
            self.stdout.write("SGA components not found. Loading data...")
            call_command("loaddata", "sga_components.json")
            self.stdout.write(self.style.SUCCESS("Data loaded successfully"))

    def has_sga_components(self):
        return any(model.objects.exists() for model in SGA_COMPONENT_MODELS)
