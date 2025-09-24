from django.core.management.base import BaseCommand
from laboratory.models import Catalog, BaseUnitValues



class Command(BaseCommand):

    help = "Create Libra unit"

    def create_unit(self):
        obj, created = Catalog.objects.get_or_create(key="units", description="Libra")
        if created:
            BaseUnitValues.objects.get_or_create(measurement_unit_base=obj, measurement_unit=obj, si_value=1)

    def handle(self, *args, **options):
        self.create_unit()
