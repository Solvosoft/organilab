from django.contrib.auth.models import Permission
from django.core.management import BaseCommand

from auth_and_perms.models import Rol

PENDING_TASK_PERMISSIONS = [
    "pending_tasks.add_pendingtask",
    "pending_tasks.change_pendingtask",
    "pending_tasks.delete_pendingtask",
    "pending_tasks.view_pendingtask",
]

WORKDAY_PERMISSIONS = [
    "risk_management.add_workday",
    "risk_management.change_workday",
    "risk_management.delete_workday",
    "risk_management.view_workday",
]

CHANGE_RISKZONE_PERMISSION = "risk_management.change_riskzone"


class Command(BaseCommand):
    help = (
        "Add pending task permissions to all roles. "
        "Also add workday permissions to roles that can change risk zones."
    )

    def get_permission(self, app_codename):
        val = app_codename.split(".")
        if len(val) == 2:
            return Permission.objects.filter(
                codename=val[1], content_type__app_label=val[0]
            ).first()
        return None

    def resolve_permissions(self, codenames, label):
        perms = []
        for codename in codenames:
            perm = self.get_permission(codename)
            if perm:
                perms.append(perm)
            else:
                self.stdout.write(
                    self.style.WARNING(f"  [{label}] Permission not found: {codename}")
                )
        return perms

    def handle(self, *args, **options):
        # --- Pending task permissions (all roles) ---
        self.stdout.write("Resolving pending task permissions...")
        pending_perms = self.resolve_permissions(PENDING_TASK_PERMISSIONS, "PendingTask")

        if not pending_perms:
            self.stdout.write(self.style.ERROR("No pending task permissions found. Aborting."))
            return

        roles = Rol.objects.prefetch_related("permissions").all()
        total = roles.count()

        if total == 0:
            self.stdout.write(self.style.WARNING("No roles found in the system."))
            return

        # --- Workday permissions (only roles with change_riskzone) ---
        self.stdout.write("Resolving workday permissions...")
        workday_perms = self.resolve_permissions(WORKDAY_PERMISSIONS, "Workday")

        change_riskzone = self.get_permission(CHANGE_RISKZONE_PERMISSION)
        if not change_riskzone:
            self.stdout.write(
                self.style.WARNING(
                    f"  Permission not found: {CHANGE_RISKZONE_PERMISSION} — "
                    "workday assignment will be skipped."
                )
            )

        # --- Apply to roles ---
        self.stdout.write(f"\nProcessing {total} role(s)...")
        workday_updated = 0

        for rol in roles:
            rol.permissions.add(*pending_perms)
            self.stdout.write(f"  [PendingTask] Updated role: '{rol.name}' (id={rol.pk})")

            if change_riskzone and workday_perms:
                has_change_riskzone = rol.permissions.filter(pk=change_riskzone.pk).exists()
                if has_change_riskzone:
                    rol.permissions.add(*workday_perms)
                    self.stdout.write(
                        f"  [Workday]     Updated role: '{rol.name}' (id={rol.pk}) — has change_riskzone"
                    )
                    workday_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. Pending task permissions added to {total} role(s). "
                f"Workday permissions added to {workday_updated} role(s) with change_riskzone."
            )
        )
