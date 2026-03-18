from django.core.management.base import BaseCommand
from django.db import transaction

from laboratory.models import ShelfObject


class Command(BaseCommand):
    help = (
        "Validate ShelfObject.in_where_laboratory against the laboratory "
        "resolved from ShelfObject -> Shelf -> Furniture -> LaboratoryRoom -> Laboratory"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of ShelfObject records to inspect",
        )
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Update in_where_laboratory when chain laboratory exists and differs",
        )
        parser.add_argument(
            "--show-ok",
            action="store_true",
            help="Show records that are already correct",
        )
        parser.add_argument(
            "--summary-only",
            action="store_true",
            help="Show only summary",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        fix = options["fix"]
        show_ok = options["show_ok"]
        summary_only = options["summary_only"]

        qs = ShelfObject.objects.select_related(
            "object",
            "in_where_laboratory",
            "shelf",
            "shelf__furniture",
            "shelf__furniture__labroom",
            "shelf__furniture__labroom__laboratory",
        ).order_by("id")

        if limit:
            qs = qs[:limit]

        total = 0
        ok = 0
        missing_chain = 0
        null_in_where = 0
        mismatch = 0
        fixed = 0

        with transaction.atomic():
            for so in qs:
                total += 1

                shelf = so.shelf
                furniture = getattr(shelf, "furniture", None) if shelf else None
                labroom = getattr(furniture, "labroom", None) if furniture else None
                chain_lab = getattr(labroom, "laboratory", None) if labroom else None

                if not chain_lab:
                    missing_chain += 1
                    if not summary_only:
                        self.stdout.write("=" * 100)
                        self.stdout.write(
                            f"ShelfObject {so.id}: chain laboratory could not be resolved"
                        )
                    continue

                if so.in_where_laboratory_id is None:
                    null_in_where += 1
                    if not summary_only:
                        self.stdout.write("=" * 100)
                        self.stdout.write(
                            f"ShelfObject {so.id}: in_where_laboratory=NULL | chain_laboratory={chain_lab.id}"
                        )
                    if fix:
                        so.in_where_laboratory = chain_lab
                        so.save(update_fields=["in_where_laboratory"])
                        fixed += 1
                    continue

                if so.in_where_laboratory_id != chain_lab.id:
                    mismatch += 1
                    if not summary_only:
                        self.stdout.write("=" * 100)
                        self.stdout.write(
                            f"ShelfObject {so.id}: in_where_laboratory={so.in_where_laboratory_id} "
                            f"| chain_laboratory={chain_lab.id}"
                        )
                    if fix:
                        so.in_where_laboratory = chain_lab
                        so.save(update_fields=["in_where_laboratory"])
                        fixed += 1
                    continue

                ok += 1
                if show_ok and not summary_only:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"OK | ShelfObject {so.id}: in_where_laboratory={so.in_where_laboratory_id}"
                        )
                    )

            if not fix:
                transaction.set_rollback(True)

        self.stdout.write("\n" + "-" * 100)
        self.stdout.write(f"Total reviewed: {total}")
        self.stdout.write(f"OK: {ok}")
        self.stdout.write(f"in_where_laboratory NULL: {null_in_where}")
        self.stdout.write(f"Mismatches: {mismatch}")
        self.stdout.write(f"Missing chain laboratory: {missing_chain}")
        self.stdout.write(f"Fixed: {fixed}")


# Example use
# python manage.py check_in_where_laboratory
# python manage.py check_in_where_laboratory --summary-only
# python manage.py check_in_where_laboratory --limit 200
# python manage.py check_in_where_laboratory --fix
