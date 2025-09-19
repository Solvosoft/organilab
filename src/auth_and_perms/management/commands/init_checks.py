from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand, call_command
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = "Load permission category"

    def handle(self, *args, **options):
        cache_config = settings.CACHES.get("default", {})
        table_name = cache_config.get("OPTIONS", {}).get("TABLE_NAME", "django_cache")
        if table_name not in connection.introspection.table_names():
            self.stdout.write("Initial data not found. Loading data...")
            # Create cache table
            call_command("createcachetable")
            # Load fixtures
            call_command("loaddata", ("sga_components.json",))
            self.stdout.write(self.style.SUCCESS("Data loaded successfully"))
