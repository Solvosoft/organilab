from collections import Counter

from django.core.management.base import BaseCommand

from laboratory.models import Object


class Command(BaseCommand):
    help = (
        "Validate Object -> ShelfObject -> Shelf -> Furniture -> "
        "LaboratoryRoom -> Laboratory chain"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of Object records to inspect",
        )
        parser.add_argument(
            "--summary-only",
            action="store_true",
            help="Print only summary",
        )
        parser.add_argument(
            "--show-ok",
            action="store_true",
            help="Show valid records too",
        )
        parser.add_argument(
            "--list-without-shelfobject",
            action="store_true",
            help="Print IDs of objects without ShelfObject",
        )
        parser.add_argument(
            "--export-without-shelfobject",
            type=str,
            help="Export IDs to file",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        summary_only = options["summary_only"]
        show_ok = options["show_ok"]
        list_without_shelfobject = []

        qs = Object.objects.select_related("organization").order_by("id")
        if limit:
            qs = qs[:limit]

        counter = Counter()
        total = 0

        for obj in qs:
            total += 1
            issues = []

            shelfobjects = list(
                obj.shelfobject_set.select_related(
                    "in_where_laboratory",
                    "shelf",
                    "shelf__furniture",
                    "shelf__furniture__labroom",
                    "shelf__furniture__labroom__laboratory",
                ).all()
            )

            if not shelfobjects:
                issues.append("Object without ShelfObject")
                counter["Object without ShelfObject"] += 1
                list_without_shelfobject.append(obj.id)
            else:
                chain_labs = set()
                chain_orgs = set()

                for so in shelfobjects:
                    shelf = so.shelf
                    furniture = getattr(shelf, "furniture", None) if shelf else None
                    labroom = getattr(furniture, "labroom", None) if furniture else None
                    laboratory = (
                        getattr(labroom, "laboratory", None) if labroom else None
                    )

                    if not shelf:
                        issues.append(f"ShelfObject {so.id} without shelf")
                        counter["ShelfObject without shelf"] += 1
                        continue
                    if not furniture:
                        issues.append(
                            f"ShelfObject {so.id} -> Shelf {shelf.id} without furniture"
                        )
                        counter["Shelf without furniture"] += 1
                        continue
                    if not labroom:
                        issues.append(
                            f"ShelfObject {so.id} -> Furniture {furniture.id} without labroom"
                        )
                        counter["Furniture without labroom"] += 1
                        continue
                    if not laboratory:
                        issues.append(
                            f"ShelfObject {so.id} -> LaboratoryRoom {labroom.id} without laboratory"
                        )
                        counter["Labroom without laboratory"] += 1
                        continue

                    chain_labs.add(laboratory.id)
                    if laboratory.organization_id:
                        chain_orgs.add(laboratory.organization_id)

                    if (
                        so.in_where_laboratory_id
                        and so.in_where_laboratory_id != laboratory.id
                    ):
                        issues.append(
                            f"ShelfObject {so.id} mismatch: "
                            f"in_where_laboratory={so.in_where_laboratory_id} "
                            f"vs chain_laboratory={laboratory.id}"
                        )
                        counter["Mismatch in_where_laboratory vs chain laboratory"] += 1

                if len(chain_labs) > 1:
                    issues.append(
                        f"Object present in multiple laboratories: {sorted(chain_labs)}"
                    )
                    counter["Object in multiple laboratories"] += 1

                if obj.organization_id:
                    if not chain_orgs:
                        issues.append(
                            f"Object organization={obj.organization_id} but no laboratory organization resolved"
                        )
                        counter["Object org without resolved lab org"] += 1
                    elif obj.organization_id not in chain_orgs:
                        issues.append(
                            f"Object organization={obj.organization_id} "
                            f"does not match laboratory organizations={sorted(chain_orgs)}"
                        )
                        counter["Object organization mismatch"] += 1

                if len(chain_orgs) > 1:
                    issues.append(
                        f"Object linked to multiple organizations through laboratories: {sorted(chain_orgs)}"
                    )
                    counter["Object in multiple organizations"] += 1

            if issues:
                if not summary_only:
                    self.stdout.write("=" * 100)
                    self.stdout.write(
                        f"Object ID={obj.id} | code={obj.code} | name={obj.name} | organization={obj.organization_id}"
                    )
                    for issue in issues:
                        self.stdout.write(f"  - {issue}")
            else:
                counter["OK"] += 1
                if show_ok and not summary_only:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"OK | Object ID={obj.id} | code={obj.code} | name={obj.name}"
                        )
                    )

        self.stdout.write("\n" + "-" * 100)
        self.stdout.write(f"Total reviewed: {total}")
        for key, value in counter.items():
            self.stdout.write(f"{key}: {value}")

        if options["list_without_shelfobject"]:
            self.stdout.write("\n" + "-" * 100)
            self.stdout.write("Objects without ShelfObject IDs:")

            # opción simple (una sola línea)
            self.stdout.write(", ".join(map(str, list_without_shelfobject)))

        if options.get("export_without_shelfobject"):
            path = options["export_without_shelfobject"]
            with open(path, "w") as f:
                for obj_id in list_without_shelfobject:
                    f.write(f"{obj_id}\n")
            self.stdout.write(f"Exported to {path}")


# Example use
# python manage.py check_shelfobject_chain
# python manage.py check_shelfobject_chain --limit 200
# python manage.py check_shelfobject_chain --summary-only
# python manage.py check_shelfobject_chain --show-ok
# python manage.py check_shelfobject_chain --list-without-shelfobject
# python manage.py check_shelfobject_chain --summary-only --list-without-shelfobject
# python manage.py check_shelfobject_chain --export-without-shelfobject missing.txt
