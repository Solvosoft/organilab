from django.core.management.base import BaseCommand

from laboratory.models import Catalog, OrganizationStructure
from risk_management.iper_defaults import seed_iper
from risk_management.models import IPERConfig, IPERRiskMatrix


class Command(BaseCommand):
    help = (
        "Siembra (idempotente) los catálogos IPER (INTE T55) en Catalog, la matriz de "
        "riesgo y una IPERConfig por cada organización raíz (parent=Null)."
    )

    def handle(self, *args, **options):
        seed_iper(Catalog, IPERRiskMatrix, IPERConfig, OrganizationStructure)
        self.stdout.write(self.style.SUCCESS("IPER catalog seeded."))
