from django.core.management.base import BaseCommand
from django.db import transaction

from laboratory.models import ShelfObject


class Command(BaseCommand):
    help = (
        "Validate ShelfObject.in_where_laboratory against the laboratory resolved from "
        "ShelfObject -> Shelf -> Furniture -> LaboratoryRoom -> Laboratory, and compare "
        "Object.organization with the laboratory organization."
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
        parser.add_argument(
            "--only-mismatch-org",
            action="store_true",
            help="Show only records where Object.organization does not match Laboratory.organization",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        fix = options["fix"]
        show_ok = options["show_ok"]
        summary_only = options["summary_only"]
        only_mismatch_org = options["only_mismatch_org"]

        qs = ShelfObject.objects.select_related(
            "object",
            "object__organization",
            "in_where_laboratory",
            "in_where_laboratory__organization",
            "shelf",
            "shelf__furniture",
            "shelf__furniture__labroom",
            "shelf__furniture__labroom__laboratory",
            "shelf__furniture__labroom__laboratory__organization",
        ).order_by("id")

        if limit:
            qs = qs[:limit]

        total = 0
        ok = 0
        missing_chain = 0
        null_in_where = 0
        mismatch_lab = 0
        mismatch_org = 0
        null_object_org = 0
        null_lab_org = 0
        fixed = 0

        with transaction.atomic():
            for so in qs:
                total += 1
                issues = []

                shelf = so.shelf
                furniture = getattr(shelf, "furniture", None) if shelf else None
                labroom = getattr(furniture, "labroom", None) if furniture else None
                chain_lab = getattr(labroom, "laboratory", None) if labroom else None

                obj = so.object
                object_org = getattr(obj, "organization", None) if obj else None
                chain_org = (
                    getattr(chain_lab, "organization", None) if chain_lab else None
                )

                if not chain_lab:
                    missing_chain += 1
                    issues.append("chain laboratory could not be resolved")
                else:
                    if so.in_where_laboratory_id is None:
                        null_in_where += 1
                        issues.append(
                            f"in_where_laboratory=NULL | chain_laboratory={chain_lab.id}"
                        )
                        if fix:
                            so.in_where_laboratory = chain_lab
                            so.save(update_fields=["in_where_laboratory"])
                            fixed += 1

                    elif so.in_where_laboratory_id != chain_lab.id:
                        mismatch_lab += 1
                        issues.append(
                            f"in_where_laboratory={so.in_where_laboratory_id} "
                            f"| chain_laboratory={chain_lab.id}"
                        )
                        if fix:
                            so.in_where_laboratory = chain_lab
                            so.save(update_fields=["in_where_laboratory"])
                            fixed += 1

                if object_org is None:
                    null_object_org += 1
                    issues.append("object.organization=NULL")

                if chain_lab and chain_org is None:
                    null_lab_org += 1
                    issues.append(
                        f"chain laboratory {chain_lab.id} has organization=NULL"
                    )

                if object_org and chain_org and object_org.id != chain_org.id:
                    mismatch_org += 1
                    issues.append(
                        f"object.organization={object_org.id} "
                        f"!= laboratory.organization={chain_org.id}"
                    )

                if only_mismatch_org and not (
                    object_org and chain_org and object_org.id != chain_org.id
                ):
                    continue

                if issues:
                    if not summary_only:
                        self.stdout.write("=" * 100)
                        self.stdout.write(
                            f"ShelfObject {so.id} | object={obj.id if obj else None} "
                            f"| object_org={object_org.id if object_org else None} "
                            f"| in_where_laboratory={so.in_where_laboratory_id} "
                            f"| chain_laboratory={chain_lab.id if chain_lab else None} "
                            f"| chain_org={chain_org.id if chain_org else None}"
                        )
                        for issue in issues:
                            self.stdout.write(f"  - {issue}")
                else:
                    ok += 1
                    if show_ok and not summary_only:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"OK | ShelfObject {so.id}: "
                                f"object_org={object_org.id if object_org else None} "
                                f"| in_where_laboratory={so.in_where_laboratory_id}"
                            )
                        )

            if not fix:
                transaction.set_rollback(True)

        self.stdout.write("\n" + "-" * 100)
        self.stdout.write(f"Total reviewed: {total}")
        self.stdout.write(f"OK: {ok}")
        self.stdout.write(f"in_where_laboratory NULL: {null_in_where}")
        self.stdout.write(f"Laboratory mismatches: {mismatch_lab}")
        self.stdout.write(f"Missing chain laboratory: {missing_chain}")
        self.stdout.write(f"Object.organization NULL: {null_object_org}")
        self.stdout.write(f"Laboratory.organization NULL: {null_lab_org}")
        self.stdout.write(f"Organization mismatches: {mismatch_org}")
        self.stdout.write(f"Fixed: {fixed}")


# Example use
# python manage.py check_in_where_laboratory
# python manage.py check_in_where_laboratory --summary-only
# python manage.py check_in_where_laboratory --limit 200
# python manage.py check_in_where_laboratory --fix
