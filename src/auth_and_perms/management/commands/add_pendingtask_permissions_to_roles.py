from django.contrib.auth.models import Permission
from django.core.management import BaseCommand

from auth_and_perms.models import Rol

PENDING_TASK_PERMISSIONS = [
    {
        "name": "Add Pending Task",
        "category": "Pending Task",
        "permission": "pending_tasks.add_pendingtask",
    },
    {
        "name": "Change Pending Task",
        "category": "Pending Task",
        "permission": "pending_tasks.change_pendingtask",
    },
    {
        "name": "Delete Pending Task",
        "category": "Pending Task",
        "permission": "pending_tasks.delete_pendingtask",
    },
    {
        "name": "View Pending Task",
        "category": "Pending Task",
        "permission": "pending_tasks.view_pendingtask",
    },
]


class Command(BaseCommand):
    help = "Add pending task permissions to all existing roles in the system"

    def get_permission(self, app_codename):
        val = app_codename.split(".")
        if len(val) == 2:
            return Permission.objects.filter(
                codename=val[1], content_type__app_label=val[0]
            ).first()
        return None

    def handle(self, *args, **options):
        permissions = []
        for item in PENDING_TASK_PERMISSIONS:
            perm = self.get_permission(item["permission"])
            if perm:
                permissions.append(perm)
                self.stdout.write(f"  Found permission: {item['permission']}")
            else:
                self.stdout.write(
                    self.style.WARNING(f"  Permission not found: {item['permission']}")
                )

        if not permissions:
            self.stdout.write(self.style.ERROR("No permissions found. Aborting."))
            return

        roles = Rol.objects.all()
        total = roles.count()

        if total == 0:
            self.stdout.write(self.style.WARNING("No roles found in the system."))
            return

        self.stdout.write(f"Adding permissions to {total} role(s)...")

        for rol in roles:
            rol.permissions.add(*permissions)
            self.stdout.write(f"  Updated role: {rol.name} (id={rol.pk})")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Pending task permissions added to {total} role(s)."
            )
        )