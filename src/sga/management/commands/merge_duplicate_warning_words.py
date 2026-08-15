from django.core.management import BaseCommand
from django.db import transaction
from django.db.models import Count

from sga.models import WarningWord, DangerIndication, SGAComplement


class Command(BaseCommand):
    help = (
        "Find WarningWord records duplicated by (name, weigth), merge all their "
        "related records into the oldest one and delete the duplicates."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only show what would be merged, without changing the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        duplicate_groups = (
            WarningWord.objects.values("name", "weigth")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
        )

        if not duplicate_groups:
            self.stdout.write(self.style.SUCCESS("No duplicated warning words found."))
            return

        for group in duplicate_groups:
            warning_words = list(
                WarningWord.objects.filter(
                    name=group["name"], weigth=group["weigth"]
                ).order_by("id")
            )
            keeper = warning_words[0]
            duplicates = warning_words[1:]

            self.stdout.write(
                f"Merging '{keeper.name}' (weigth={keeper.weigth}): "
                f"keeping id={keeper.pk}, removing ids="
                f"{[dup.pk for dup in duplicates]}"
            )

            if dry_run:
                continue

            with transaction.atomic():
                for dup in duplicates:
                    DangerIndication.objects.filter(warning_words=dup).update(
                        warning_words=keeper
                    )
                    SGAComplement.objects.filter(warningword=dup).update(
                        warningword=keeper
                    )
                    dup.delete()

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run: no changes were made."))
        else:
            self.stdout.write(self.style.SUCCESS("Duplicated warning words merged."))