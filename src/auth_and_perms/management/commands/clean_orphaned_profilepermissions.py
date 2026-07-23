from django.core.management.base import BaseCommand

from auth_and_perms.models import ProfilePermission


class Command(BaseCommand):
    help = (
        "Remove ProfilePermission rows whose content_object no longer exists "
        "(dangling GenericForeignKey left behind when the referenced "
        "Laboratory/OrganizationStructure/etc was deleted)"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry",
            action="store_true",
            help="Do a dry run, not actually deleting anything",
        )

    def handle(self, *args, **options):
        orphan_pks = []
        for pp in ProfilePermission.objects.select_related("content_type").iterator():
            if pp.content_type_id and pp.content_object is None:
                orphan_pks.append(pp.pk)
                self.stdout.write(
                    f"Orphaned ProfilePermission {pp.pk}: "
                    f"{pp.content_type} #{pp.object_id} (profile={pp.profile_id})"
                )

        if options["dry"]:
            self.stdout.write(
                f"DRY RUN: {len(orphan_pks)} orphaned ProfilePermission rows NOT deleted"
            )
            return

        if orphan_pks:
            ProfilePermission.objects.filter(pk__in=orphan_pks).delete()
        self.stdout.write(f"{len(orphan_pks)} orphaned ProfilePermission rows deleted")
