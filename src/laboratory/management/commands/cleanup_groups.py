from django.contrib.auth.models import Group, Permission, User
from django.core.management import BaseCommand


GROUPS_TO_DELETE = [
    "Manage Roles Permissions",
    "Professor",
    "Student",
]
PROFILE_GROUP = "Profile"
PROFILE_PERM = ("auth_and_perms", "change_own_profile")


class Command(BaseCommand):
    help = "Delete unused groups and add change_profile permission to Profile group"

    def handle(self, *args, **options):
        for name in GROUPS_TO_DELETE:
            deleted, _ = Group.objects.filter(name=name).delete()
            if deleted:
                self.stdout.write(self.style.SUCCESS(f"Deleted group '{name}'"))
            else:
                self.stdout.write(f"Group '{name}' not found, skipping")

        profile_group, created = Group.objects.get_or_create(name=PROFILE_GROUP)
        if created:
            self.stdout.write(self.style.WARNING(f"Group '{PROFILE_GROUP}' did not exist, created"))

        perm = Permission.objects.filter(
            content_type__app_label=PROFILE_PERM[0],
            codename=PROFILE_PERM[1],
        ).first()
        if perm is None:
            self.stderr.write(self.style.ERROR(f"Permission '{'.'.join(PROFILE_PERM)}' not found"))
            return

        if not profile_group.permissions.filter(pk=perm.pk).exists():
            profile_group.permissions.add(perm)
            self.stdout.write(self.style.SUCCESS(f"Added '{'.'.join(PROFILE_PERM)}' to group '{PROFILE_GROUP}'"))
        else:
            self.stdout.write(f"'{'.'.join(PROFILE_PERM)}' already in '{PROFILE_GROUP}', skipping")

        required_groups = list(Group.objects.filter(name__in=["Profile", "PendingTasks"]))
        for user in User.objects.all():
            for group in required_groups:
                if not user.groups.filter(pk=group.pk).exists():
                    user.groups.add(group)
        self.stdout.write(self.style.SUCCESS(f"Ensured all users have groups: {[g.name for g in required_groups]}"))
