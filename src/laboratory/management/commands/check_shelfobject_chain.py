from collections import Counter

from django.core.management.base import BaseCommand

from laboratory.models import ShelfObject


class Command(BaseCommand):
    help = (
        "Validate ShelfObject relationship chain: "
        "ShelfObject -> Shelf -> Furniture -> LaboratoryRoom -> Laboratory"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of ShelfObject records to inspect",
        )
        parser.add_argument(
            "--show-ok",
            action="store_true",
            help="Also print records with a valid chain",
        )
        parser.add_argument(
            "--summary-only",
            action="store_true",
            help="Print only summary",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        show_ok = options["show_ok"]
        summary_only = options["summary_only"]

        qs = ShelfObject.objects.select_related(
            "shelf",
            "shelf__furniture",
            "shelf__furniture__labroom",
            "shelf__furniture__labroom__laboratory",
            "in_where_laboratory",
            "object",
        ).order_by("id")

        if limit:
            qs = qs[:limit]

        counter = Counter()
        total = 0

        for so in qs:
            total += 1
            issues = []

            shelf = so.shelf
            furniture = getattr(shelf, "furniture", None) if shelf else None
            labroom = getattr(furniture, "labroom", None) if furniture else None
            laboratory = getattr(labroom, "laboratory", None) if labroom else None

            if not shelf:
                issues.append("ShelfObject -> shelf = NULL")
                counter["ShelfObject without shelf"] += 1
            elif not furniture:
                issues.append(f"Shelf {shelf.id} -> furniture = NULL")
                counter["Shelf without furniture"] += 1
            elif not labroom:
                issues.append(f"Furniture {furniture.id} -> labroom = NULL")
                counter["Furniture without labroom"] += 1
            elif not laboratory:
                issues.append(f"LaboratoryRoom {labroom.id} -> laboratory = NULL")
                counter["Labroom without laboratory"] += 1

            if (
                so.in_where_laboratory_id
                and laboratory
                and so.in_where_laboratory_id != laboratory.id
            ):
                issues.append(
                    f"Mismatch: in_where_laboratory={so.in_where_laboratory_id} "
                    f"but chain laboratory={laboratory.id}"
                )
                counter["Mismatch in_where_laboratory vs chain laboratory"] += 1

            if not issues:
                counter["OK"] += 1
                if show_ok and not summary_only:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"OK | ShelfObject {so.id} -> Shelf {shelf.id} -> "
                            f"Furniture {furniture.id} -> LabRoom {labroom.id} -> "
                            f"Laboratory {laboratory.id}"
                        )
                    )
                continue

            if not summary_only:
                self.stdout.write("=" * 100)
                self.stdout.write(
                    f"ShelfObject ID={so.id} | object={so.object_id} | "
                    f"in_where_laboratory={so.in_where_laboratory_id}"
                )
                for issue in issues:
                    self.stdout.write(f"  - {issue}")

        self.stdout.write("\n" + "-" * 100)
        self.stdout.write(f"Total reviewed: {total}")
        for key, value in counter.items():
            self.stdout.write(f"{key}: {value}")


# Example use
# python manage.py check_shelfobject_chain
# python manage.py check_shelfobject_chain --limit 200
# python manage.py check_shelfobject_chain --summary-only
# python manage.py check_shelfobject_chain --show-ok
