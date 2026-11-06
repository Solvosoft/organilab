from django.core.management.base import BaseCommand
from laboratory.models import Catalog, BaseUnitValues


class Command(BaseCommand):

    help = "Create Libra unit"

    def create_unit(self):
        obj, created = Catalog.objects.get_or_create(key="units", description="Libra")
        kilograms = Catalog.objects.filter(key="units", description="Kilogramos").first()
        if created and kilograms is not None:
            BaseUnitValues.objects.get_or_create(
                measurement_unit=obj, defaults={"measurement_unit_base": kilograms, "si_value": 2.20462}
            )

    def handle(self, *args, **options):
        self.create_unit()
