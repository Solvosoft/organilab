from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

from laboratory.models import Laboratory, OrganizationStructure, \
    OrganizationStructureRelations


class Command(BaseCommand):
    help = "Migra los laboratorios a la organización root y crea las relaciones"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra los cambios sin ejecutarlos",
        )

    def create_organization_structure(self, org, lab, relations_created):
        lab_content_type = ContentType.objects.get_for_model(Laboratory)

        relation, created = OrganizationStructureRelations.objects.get_or_create(
            organization=org,
            content_type=lab_content_type,
            object_id=lab.pk,
        )

        if created:
            relations_created += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"    ✓ Relación creada con {org.name}")
            )
        else:
            self.stdout.write(
                self.style.NOTICE(
                    f"    - Relación ya existía con {org.name}")
            )

        return relations_created

    def handle(self, *args, **options):
        dry_run = options["dry_run"]


        laboratories = Laboratory.objects.select_related("organization").exclude(
            organization__isnull=True
        )

        total = laboratories.count()
        migrated = 0
        relations_created = 0
        skipped = 0

        self.stdout.write(f"Procesando {total} laboratorios...")

        for lab in laboratories:
            original_org = lab.organization

            if original_org is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"  [{lab.pk}] {lab.name} - Sin organización, saltando")
                )
                skipped += 1
                continue

            root_org = original_org.root

            if original_org.pk == root_org.pk:
                self.stdout.write(
                    self.style.NOTICE(
                        f"  [{lab.pk}] {lab.name} - Ya está en root ({root_org.name})")
                )
                skipped += 1
                continue

            self.stdout.write(
                f"  [{lab.pk}] {lab.name}: {original_org.name} -> {root_org.name}"
            )

            if not dry_run:

                relations_created = self.create_organization_structure(original_org, lab, relations_created)
                relations_created = self.create_organization_structure(root_org, lab, relations_created)

                lab.organization = root_org
                lab.save(update_fields=["organization"])
                migrated += 1
                self.stdout.write(
                    self.style.SUCCESS(f"    ✓ Organización cambiada a {root_org.name}")
                )

        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Total laboratorios: {total}")
        self.stdout.write(f"Migrados: {migrated}")
        self.stdout.write(f"Relaciones creadas: {relations_created}")
        self.stdout.write(f"Saltados: {skipped}")

        if dry_run:
            self.stdout.write(
                self.style.WARNING("\n[DRY-RUN] No se ejecutaron cambios reales")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\n✓ Migración completada")
            )
