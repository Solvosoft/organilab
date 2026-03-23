from django.core.management.base import BaseCommand
from django.db.models import Count

from risk_management.models import Buildings, IncidentReport, Structure


class Command(BaseCommand):
    help = "Merge duplicate Buildings with the same name, keeping the oldest (lowest PK)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview what would be merged without making changes.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        duplicates = (
            Buildings.objects.values("name")
            .annotate(c=Count("pk"))
            .filter(c__gt=1)
            .order_by("-c")
        )

        if not duplicates.exists():
            self.stdout.write(self.style.SUCCESS("No duplicate Buildings found."))
            return

        total_merged = 0
        total_deleted = 0

        for group in duplicates:
            name = group["name"]
            buildings = Buildings.objects.filter(name=name).order_by("pk")
            survivor = buildings.first()
            to_delete = buildings.exclude(pk=survivor.pk)
            count = to_delete.count()

            self.stdout.write(f"\n{'=' * 60}")
            self.stdout.write(f"  {name} — {count + 1} buildings, keeping PK={survivor.pk}")

            for dupe in to_delete:
                labs = list(dupe.laboratories.all())
                regents = list(dupe.regents.all())
                nearby = list(dupe.nearby_buildings.exclude(pk=survivor.pk))
                riskzones = list(dupe.riskzone_set.all())
                incidents = list(dupe.incident_buildings.all())
                structures = list(dupe.structura_buildings.all())
                near_as = list(dupe.near_buildings_as.exclude(pk=survivor.pk))

                self.stdout.write(
                    f"    PK={dupe.pk}: "
                    f"{len(labs)} labs, "
                    f"{len(regents)} regents, "
                    f"{len(riskzones)} riskzones, "
                    f"{len(incidents)} incidents, "
                    f"{len(structures)} structures, "
                    f"{len(nearby)} nearby"
                )

                if not dry_run:
                    survivor.laboratories.add(*labs)
                    survivor.regents.add(*regents)
                    survivor.nearby_buildings.add(*nearby)
                    for rz in riskzones:
                        rz.buildings.add(survivor)
                    for incident in incidents:
                        incident.buildings.add(survivor)
                    for structure in structures:
                        structure.buildings.add(survivor)
                    for b in near_as:
                        b.nearby_buildings.add(survivor)

            if not dry_run:
                to_delete.delete()

            total_merged += 1
            total_deleted += count

        action = "Would delete" if dry_run else "Deleted"
        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} {total_deleted} duplicate buildings across {total_merged} groups."
            )
        )
