from django.core.management.base import BaseCommand

from laboratory.models import Laboratory
from risk_management.models import RiskZone


class Command(BaseCommand):
    help = "Assign laboratories to risk zones based on their buildings relationship."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview assignments without making changes.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        total_assigned = 0

        for rz in (
            RiskZone.objects.prefetch_related("buildings", "laboratories")
            .all()
            .order_by("name")
        ):
            labs = Laboratory.objects.filter(
                buildings__in=rz.buildings.all()
            ).distinct()

            new_labs = labs.exclude(pk__in=rz.laboratories.all())

            if not new_labs.exists():
                continue

            lab_names = list(new_labs.values_list("name", flat=True))
            self.stdout.write(f"\n{rz.name}:")
            for name in lab_names:
                self.stdout.write(f"  + {name}")

            if not dry_run:
                rz.laboratories.add(*new_labs)

            total_assigned += len(lab_names)

        action = "Would assign" if dry_run else "Assigned"
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{action} {total_assigned} laboratories to risk zones."
            )
        )
