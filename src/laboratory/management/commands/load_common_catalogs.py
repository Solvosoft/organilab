from django.core.management.base import BaseCommand, CommandError

from laboratory.catalog.utils import create_catalog
from laboratory.models import Catalog


class Command(BaseCommand):
    help = 'Create catalogs'

    def handle(self, *args, **options):
        create_catalog(Catalog)