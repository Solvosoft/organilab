from django.core.management.base import BaseCommand
from django.db import transaction

from sga.models import SubstanceCharacteristics


class Command(BaseCommand):
    help = (
        "Elimina las SubstanceCharacteristics huérfanas: sin sustancia SGA y sin "
        "objeto de laboratorio. Se generan cuando se borra un Object, porque "
        "object_related es SET_NULL y la fila sobrevive sin dueño."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra cuántas se borrarían sin borrar nada.",
        )

    def handle(self, *args, **options):
        orphans = SubstanceCharacteristics.objects.filter(
            substance__isnull=True, object_related__isnull=True
        )
        total = orphans.count()

        if not total:
            self.stdout.write(self.style.SUCCESS("No hay características huérfanas."))
            return

        if options["dry_run"]:
            self.stdout.write(
                "Se borrarían %d características huérfanas (pks: %s)."
                % (total, list(orphans.values_list("pk", flat=True)[:20]))
            )
            return

        with transaction.atomic():
            deleted, _detail = orphans.delete()

        self.stdout.write(
            self.style.SUCCESS(
                "Borradas %d características huérfanas (%d filas en total con sus "
                "relaciones)." % (total, deleted)
            )
        )
