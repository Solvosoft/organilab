from django.contrib.auth.models import Group, Permission, User
from django.core.management import BaseCommand


GROUP_NAME = "SGAView"
GROUP_PERMISSIONS = [
    ("msds", "view_msdsobject"),
]


class Command(BaseCommand):
    help = "Create SGAView group with substance view + SDS download permissions and assign to all users"

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name=GROUP_NAME)
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created group '{GROUP_NAME}'"))
        else:
            self.stdout.write(f"Group '{GROUP_NAME}' already exists, updating permissions")
            group.permissions.clear()

        for app_label, codename in GROUP_PERMISSIONS:
            perm = Permission.objects.filter(
                content_type__app_label=app_label,
                codename=codename,
            ).first()
            if perm is None:
                self.stderr.write(self.style.ERROR(f"Permission '{app_label}.{codename}' not found"))
                continue
            group.permissions.add(perm)
            self.stdout.write(self.style.SUCCESS(f"Added '{app_label}.{codename}' to '{GROUP_NAME}'"))

        assigned = 0
        for user in User.objects.all():
            if not user.groups.filter(pk=group.pk).exists():
                user.groups.add(group)
                assigned += 1
        self.stdout.write(self.style.SUCCESS(f"Assigned '{GROUP_NAME}' to {assigned} user(s) (skipped {User.objects.count() - assigned} already assigned)"))
