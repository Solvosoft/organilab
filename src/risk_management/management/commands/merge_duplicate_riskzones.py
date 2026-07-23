from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models import Count, Max

from risk_management.models import RiskZone, EstablishmentLogs, IncidentReport


class Command(BaseCommand):
    help = "Merge duplicate RiskZones with the same name, keeping the oldest (lowest PK)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview what would be merged without making changes.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        rz_ct = ContentType.objects.get_for_model(RiskZone)

        duplicates = (
            RiskZone.objects.values("name")
            .annotate(c=Count("pk"))
            .filter(c__gt=1)
            .order_by("-c")
        )

        if not duplicates.exists():
            self.stdout.write(self.style.SUCCESS("No duplicate RiskZones found."))
            return

        total_merged = 0
        total_deleted = 0

        for group in duplicates:
            name = group["name"]
            zones = RiskZone.objects.filter(name=name).order_by("pk")
            survivor = zones.first()
            to_delete = zones.exclude(pk=survivor.pk)
            count = to_delete.count()

            self.stdout.write(f"\n{'=' * 60}")
            self.stdout.write(f"  {name} — {count + 1} zones, keeping PK={survivor.pk}")

            max_workers = survivor.num_workers
            max_priority = survivor.priority

            for dupe in to_delete:
                labs = list(dupe.laboratories.all())
                buildings = list(dupe.buildings.all())
                incidents = IncidentReport.objects.filter(risk_zone=dupe)
                logs = EstablishmentLogs.objects.filter(content_type=rz_ct, object_id=dupe.pk)

                self.stdout.write(
                    f"    PK={dupe.pk}: "
                    f"{len(labs)} labs, "
                    f"{len(buildings)} buildings, "
                    f"{incidents.count()} incidents, "
                    f"{logs.count()} logs"
                )

                if not dry_run:
                    survivor.laboratories.add(*labs)
                    survivor.buildings.add(*buildings)
                    incidents.update(risk_zone=survivor)
                    logs.update(object_id=survivor.pk)

                if dupe.num_workers > max_workers:
                    max_workers = dupe.num_workers
                if dupe.priority > max_priority:
                    max_priority = dupe.priority

            if not dry_run:
                survivor.num_workers = max_workers
                survivor.priority = max_priority
                survivor.save(update_fields=["num_workers", "priority"])
                to_delete.delete()

            total_merged += 1
            total_deleted += count

        action = "Would delete" if dry_run else "Deleted"
        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} {total_deleted} duplicate zones across {total_merged} groups."
            )
        )
