from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from auth_and_perms.models import ProfilePermission
from laboratory.models import (
    Laboratory,
    OrganizationStructureRelations,
    UserOrganization,
)


class Command(BaseCommand):
    help = "Migrate ProfilePermission to include organization field"

    def handle(self, *args, **options):
        lab_ct = ContentType.objects.get_for_model(Laboratory)

        # ProfilePermissions de laboratorios sin organización asignada
        permissions = ProfilePermission.objects.filter(
            content_type=lab_ct,
            organization__isnull=True,
        )

        updated = 0
        for perm in permissions:
            lab_pk = perm.object_id

            # Buscar la relación org-lab
            relations = OrganizationStructureRelations.objects.filter(
                content_type=lab_ct,
                object_id=lab_pk,
            )

            for relation in relations:
                if UserOrganization.objects.filter(
                    user=perm.profile.user,
                    organization=relation.organization,
                ).exists():
                    perm.organization = relation.organization
                    perm.save(update_fields=["organization"])
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Updated {updated} ProfilePermission records with organization"
            )
        )
