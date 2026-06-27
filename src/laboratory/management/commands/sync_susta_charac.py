from django.core.management.base import BaseCommand
from laboratory.models import SustanceCharacteristics


class Command(BaseCommand):

    help = "t"

    def migrate_susta(self):
        old = (
            SustanceCharacteristics.objects.using("oldDB")
            .filter(cas_id_number__isnull=False)
            .exclude(cas_id_number="")
        )

        for sus in old:
            if sus.pk not in [
                944,
                1521,
                242,
                923,
                633,
                586,
                1622,
                504,
                408,
                288,
                968,
                1630,
                833,
                795,
                660,
            ]:
                sux = SustanceCharacteristics.objects.using("default").filter(pk=sus.pk)
                for s in sux:
                    if sus.security_sheet:
                        s.security_sheet = sus.security_sheet
                        s.save()

    def handle(self, *args, **options):
        self.migrate_susta()
