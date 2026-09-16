from django.core.management.base import BaseCommand

from ambiental.ambiental_defaults import seed_ambiental
from laboratory.models import Catalog


class Command(BaseCommand):
    help = "Siembra (idempotente) los catálogos del módulo ambiental en Catalog."

    def handle(self, *args, **options):
        seed_ambiental(Catalog)
        self.stdout.write(self.style.SUCCESS("Ambiental catalog seeded."))
