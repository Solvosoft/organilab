from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand

from auth_and_perms.management.commands.urlname_permissions import URLNAME_PERMISSIONS
from auth_and_perms.models import Rol

PENDING_TASK_PERMISSIONS = [
    "pending_tasks.add_pendingtask",
    "pending_tasks.change_pendingtask",
    "pending_tasks.delete_pendingtask",
    "pending_tasks.view_pendingtask",
]


class Command(BaseCommand):
    help = "Check that all roles and permission groups are correctly configured"

    def get_permission(self, app_codename):
        val = app_codename.split(".")
        if len(val) == 2:
            return Permission.objects.filter(
                codename=val[1], content_type__app_label=val[0]
            ).first()
        return None

    def check_urlname_permissions(self):
        self.stdout.write("\n--- URLNAME_PERMISSIONS (urlname → DB) ---")
        missing = []
        seen = set()
        for url_name, items in URLNAME_PERMISSIONS.items():
            for item in items:
                codename = item["permission"]
                if codename in seen:
                    continue
                seen.add(codename)
                if not self.get_permission(codename):
                    missing.append((url_name, codename))

        if missing:
            for url_name, codename in missing:
                self.stdout.write(
                    self.style.ERROR(f"  [MISSING] {codename}  (used in '{url_name}')")
                )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"  All {len(seen)} unique permissions exist in DB."
                )
            )
        return missing

    def check_pendingtasks_group(self):
        self.stdout.write("\n--- Group: PendingTasks ---")
        group = Group.objects.filter(name="PendingTasks").first()
        if not group:
            self.stdout.write(self.style.ERROR("  [MISSING] Group 'PendingTasks' does not exist."))
            return False

        group_perms = set(
            f"{p.content_type.app_label}.{p.codename}"
            for p in group.permissions.all()
        )
        ok = True
        for codename in PENDING_TASK_PERMISSIONS:
            if codename in group_perms:
                self.stdout.write(self.style.SUCCESS(f"  [OK] {codename}"))
            else:
                self.stdout.write(self.style.ERROR(f"  [MISSING] {codename}"))
                ok = False
        return ok

    def check_roles(self):
        self.stdout.write("\n--- Roles (Rol model) ---")
        roles = Rol.objects.prefetch_related("permissions").all()
        if not roles.exists():
            self.stdout.write(self.style.WARNING("  No roles found in the system."))
            return

        issues = []
        for rol in roles:
            perm_count = rol.permissions.count()
            # Check for any permission in the role that no longer exists
            # (orphaned M2M entries would raise, so we just report count)
            self.stdout.write(f"  Rol [{rol.pk}] '{rol.name}' — {perm_count} permission(s)")

            # Check if pending task perms are present
            role_perm_codes = set(
                f"{p.content_type.app_label}.{p.codename}"
                for p in rol.permissions.all()
            )
            pending_missing = [
                c for c in PENDING_TASK_PERMISSIONS if c not in role_perm_codes
            ]
            if pending_missing:
                for c in pending_missing:
                    self.stdout.write(
                        self.style.WARNING(f"    [WARN] Missing pending task perm: {c}")
                    )
                issues.append(rol)

        if issues:
            self.stdout.write(
                self.style.WARNING(
                    f"\n  {len(issues)} role(s) are missing pending task permissions. "
                    "Run: python manage.py add_pendingtask_permissions_to_roles"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n  All {roles.count()} role(s) have pending task permissions."
                )
            )

    def check_profile_group(self):
        self.stdout.write("\n--- Group: Profile ---")
        group = Group.objects.filter(name="Profile").first()
        if not group:
            self.stdout.write(self.style.WARNING("  Group 'Profile' does not exist."))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"  [OK] Exists with {group.permissions.count()} permission(s)."
                )
            )

    def check_register_organization_group(self):
        self.stdout.write("\n--- Group: RegisterOrganization ---")
        group = Group.objects.filter(name="RegisterOrganization").first()
        if not group:
            self.stdout.write(
                self.style.WARNING("  Group 'RegisterOrganization' does not exist.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"  [OK] Exists with {group.permissions.count()} permission(s)."
                )
            )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== Role & Permission Health Check ==="))

        missing_urlname = self.check_urlname_permissions()
        self.check_pendingtasks_group()
        self.check_roles()
        self.check_profile_group()
        self.check_register_organization_group()

        self.stdout.write("\n" + "=" * 40)
        if missing_urlname:
            self.stdout.write(
                self.style.ERROR(
                    f"RESULT: {len(missing_urlname)} permission(s) missing from DB. "
                    "Run migrations and/or load_urlname_permissions."
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("RESULT: All checks passed."))
