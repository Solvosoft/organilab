from django.core.management.base import BaseCommand, CommandError
from laboratory.models import OrganizationStructure, Object


class Command(BaseCommand):
    help = "Update all Object records to the specified organization"

    def add_arguments(self, parser):
        parser.add_argument(
            "organization_pk",
            type=int,
            help="Primary key of the target organization",
        )

    def handle(self, *args, **options):
        org_pk = options["organization_pk"]

        try:
            organization = OrganizationStructure.objects.get(pk=org_pk)
        except OrganizationStructure.DoesNotExist:
            raise CommandError(f"Organization with pk={org_pk} does not exist")

        count = Object.objects.count()
        Object.objects.update(organization=organization)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {count} Object(s) to organization '{organization}'"
            )
        )