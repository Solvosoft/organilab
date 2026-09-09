from django.core.management.base import BaseCommand

from laboratory.catalog.utils import create_catalog
from laboratory.models import Catalog


class Command(BaseCommand):
    help = "Create catalogs (idempotent: only adds the entries that are missing)"

    def handle(self, *args, **options):
        created = create_catalog(Catalog)
        self.stdout.write(
            self.style.SUCCESS("Catalogs ready: %d created, rest already present."
                               % created)
        )
