from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from laboratory.models import Object


class Command(BaseCommand):
    help = "Check a list of Object IDs from a file against the current database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            required=True,
            help="Path to file containing Object IDs, one per line",
        )
        parser.add_argument(
            "--show-ok",
            action="store_true",
            help="Show objects that exist and have ShelfObject",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"])
        show_ok = options["show_ok"]

        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")

        ids = []
        for line in file_path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ids.append(int(line))
            except ValueError:
                self.stdout.write(self.style.WARNING(f"Skipping invalid ID: {line}"))

        if not ids:
            raise CommandError("No valid IDs found in file")

        total = len(ids)
        found = 0
        not_found = []
        without_shelfobject = []
        with_shelfobject = []

        objects = {
            obj.id: obj
            for obj in Object.objects.filter(id__in=ids).prefetch_related(
                "shelfobject_set"
            )
        }

        for obj_id in ids:
            obj = objects.get(obj_id)

            if not obj:
                not_found.append(obj_id)
                continue

            found += 1

            if obj.shelfobject_set.exists():
                with_shelfobject.append(obj_id)
                if show_ok:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"OK | Object {obj.id} | code={obj.code} | name={obj.name}"
                        )
                    )
            else:
                without_shelfobject.append(obj_id)
                self.stdout.write(
                    f"MISSING SHELFOBJECT | Object {obj.id} | code={obj.code} | name={obj.name}"
                )

        self.stdout.write("\n" + "-" * 80)
        self.stdout.write(f"IDs in file: {total}")
        self.stdout.write(f"Found in current DB: {found}")
        self.stdout.write(f"Not found: {len(not_found)}")
        self.stdout.write(f"Without ShelfObject: {len(without_shelfobject)}")
        self.stdout.write(f"With ShelfObject: {len(with_shelfobject)}")

        if not_found:
            self.stdout.write("\nNot found IDs:")
            self.stdout.write(", ".join(map(str, not_found)))

        if without_shelfobject:
            self.stdout.write("\nIDs still without ShelfObject:")
            self.stdout.write(", ".join(map(str, without_shelfobject)))

            Path("recovered_with_shelfobject.txt").write_text(
                "\n".join(map(str, with_shelfobject)) + "\n"
            )

            self.stdout.write("Exported: recovered_with_shelfobject.txt")


# python manage.py check_objects_from_file --file missing.txt
