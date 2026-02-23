from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from laboratory.models import Laboratory, OrganizationStructure, \
    OrganizationStructureRelations, UserOrganization


class Command(BaseCommand):
    help = "Migra los laboratorios y usuarios a la organización root y crea las relaciones"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra los cambios sin ejecutarlos",
        )

    def create_organization_relation(self, org, obj, content_type, relations_created):
        """Crea una relación OrganizationStructureRelations si no existe."""
        relation, created = OrganizationStructureRelations.objects.get_or_create(
            organization=org,
            content_type=content_type,
            object_id=obj.pk,
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

    def migrate_laboratories(self, dry_run):
        """Migra los laboratorios al root."""
        self.stdout.write(self.style.HTTP_INFO("\n=== MIGRANDO LABORATORIOS ===\n"))

        lab_content_type = ContentType.objects.get_for_model(Laboratory)
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
                relations_created = self.create_organization_relation(
                    original_org, lab, lab_content_type, relations_created
                )
                relations_created = self.create_organization_relation(
                    root_org, lab, lab_content_type, relations_created
                )
                lab.organization = root_org
                lab.save(update_fields=["organization"])
                migrated += 1
                self.stdout.write(
                    self.style.SUCCESS(f"    ✓ Organización cambiada a {root_org.name}")
                )

        return {
            "total": total,
            "migrated": migrated,
            "relations_created": relations_created,
            "skipped": skipped,
        }

    def migrate_user_organizations(self, dry_run):
        """Migra los UserOrganization al root."""
        self.stdout.write(
            self.style.HTTP_INFO("\n=== MIGRANDO USUARIOS DE ORGANIZACIÓN ===\n"))

        user_org_content_type = ContentType.objects.get_for_model(UserOrganization)
        user_orgs = UserOrganization.objects.select_related(
            "organization", "user"
        ).exclude(organization__isnull=True)

        total = user_orgs.count()
        migrated = 0
        relations_created = 0
        skipped = 0

        self.stdout.write(f"Procesando {total} usuarios de organización...")

        for user_org in user_orgs:
            original_org = user_org.organization
            user_display = user_org.user.username if user_org.user else f"ID:{user_org.pk}"

            if original_org is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"  [{user_org.pk}] {user_display} - Sin organización, saltando")
                )
                skipped += 1
                continue

            root_org = original_org.root

            if original_org.pk == root_org.pk:
                self.stdout.write(
                    self.style.NOTICE(
                        f"  [{user_org.pk}] {user_display} - Ya está en root ({root_org.name})")
                )
                skipped += 1
                continue

            type_display = dict(UserOrganization.TYPE_IN_ORG).get(
                user_org.type_in_organization, "Desconocido"
            )
            self.stdout.write(
                f"  [{user_org.pk}] {user_display} ({type_display}): "
                f"{original_org.name} -> {root_org.name}"
            )

            if not dry_run:
                relations_created = self.create_organization_relation(
                    original_org, user_org, user_org_content_type, relations_created
                )
                relations_created = self.create_organization_relation(
                    root_org, user_org, user_org_content_type, relations_created
                )

                user_org.organization = root_org
                user_org.save(update_fields=["organization"])
                migrated += 1
                self.stdout.write(
                    self.style.SUCCESS(f"    ✓ Organización cambiada a {root_org.name}")
                )

        return {
            "total": total,
            "migrated": migrated,
            "relations_created": relations_created,
            "skipped": skipped,
        }

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        lab_stats = self.migrate_laboratories(dry_run)

        user_stats = self.migrate_user_organizations(dry_run)

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.HTTP_INFO("RESUMEN FINAL"))
        self.stdout.write("=" * 60)

        self.stdout.write("\nLaboratorios:")
        self.stdout.write(f"  Total: {lab_stats['total']}")
        self.stdout.write(f"  Migrados: {lab_stats['migrated']}")
        self.stdout.write(f"  Relaciones creadas: {lab_stats['relations_created']}")
        self.stdout.write(f"  Saltados: {lab_stats['skipped']}")

        self.stdout.write("\nUsuarios de Organización:")
        self.stdout.write(f"  Total: {user_stats['total']}")
        self.stdout.write(f"  Migrados: {user_stats['migrated']}")
        self.stdout.write(f"  Relaciones creadas: {user_stats['relations_created']}")
        self.stdout.write(f"  Saltados: {user_stats['skipped']}")

        total_migrated = lab_stats['migrated'] + user_stats['migrated']
        total_relations = lab_stats['relations_created'] + user_stats[
            'relations_created']

        self.stdout.write("\nTotales:")
        self.stdout.write(f"  Objetos migrados: {total_migrated}")
        self.stdout.write(f"  Relaciones creadas: {total_relations}")

        if dry_run:
            self.stdout.write(
                self.style.WARNING("\n[DRY-RUN] No se ejecutaron cambios reales")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\n✓ Migración completada")
            )
