from django.contrib.auth.models import Group, Permission, User
from django.core.management import BaseCommand

PENDING_TASK_PERMISSIONS = [
    "pending_tasks.add_pendingtask",
    "pending_tasks.change_pendingtask",
    "pending_tasks.delete_pendingtask",
    "pending_tasks.view_pendingtask",
]

GROUP_NAME = "PendingTasks"


class Command(BaseCommand):
    help = (
        "Create the PendingTasks group with pending task permissions "
        "and assign it to all existing users"
    )

    def get_permission(self, app_codename):
        val = app_codename.split(".")
        if len(val) == 2:
            return Permission.objects.filter(
                codename=val[1], content_type__app_label=val[0]
            ).first()
        return None

    def handle(self, *args, **options):
        # 1. Create or get the group
        group, created = Group.objects.get_or_create(name=GROUP_NAME)
        if created:
            self.stdout.write(f"Group '{GROUP_NAME}' created.")
        else:
            self.stdout.write(f"Group '{GROUP_NAME}' already exists.")

        # 2. Add pending task permissions to the group
        permissions = []
        for app_codename in PENDING_TASK_PERMISSIONS:
            perm = self.get_permission(app_codename)
            if perm:
                permissions.append(perm)
                self.stdout.write(f"  Found permission: {app_codename}")
            else:
                self.stdout.write(
                    self.style.WARNING(f"  Permission not found: {app_codename}")
                )

        if permissions:
            group.permissions.add(*permissions)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Added {len(permissions)} permission(s) to group '{GROUP_NAME}'."
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    "No permissions found. Make sure pending_tasks migrations have been applied."
                )
            )
            return

        # 3. Add the group to all existing users
        users = User.objects.all()
        total = users.count()

        if total == 0:
            self.stdout.write(self.style.WARNING("No users found in the system."))
            return

        self.stdout.write(f"Assigning group '{GROUP_NAME}' to {total} user(s)...")
        for user in users:
            user.groups.add(group)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Group '{GROUP_NAME}' assigned to {total} user(s)."
            )
        )
