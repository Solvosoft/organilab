from django.contrib.auth.models import Group, Permission, User
from django.core.management import BaseCommand

from auth_and_perms.models import Rol
from laboratory.models import OrganizationStructure, UserOrganization


SOURCE_ROL = "Administrador de Laboratorio"
CLONE_ROL = "Administrativo Auxiliar"
PERMS_TO_REMOVE = [
    "laboratory.view_organizationstructure",
    "laboratory.change_object",
    "laboratory.can_manage_org_permissions",
]
REGISTER_ORG_GROUP = "RegisterOrganization"
EXEMPT_EMAILS = [
    "wendy.umana.herrera@una.cr",
    "daniela.guerrero.mayorga@est.una.ac.cr",
]
LIGIA_EMAIL = "lsoli@una.cr"
LIGIA_EXEMPT_ORG = "Laboratorios de Docencia Universidad Nacional"


class Command(BaseCommand):
    help = "Remove permissions from 'Administrador de Laboratorio' and clone it as 'Administrativo Auxiliar'"

    def handle(self, *args, **options):
        source = Rol.objects.filter(name=SOURCE_ROL).first()
        if source is None:
            self.stderr.write(self.style.ERROR(f"Rol '{SOURCE_ROL}' not found"))
            return

        for perm_str in PERMS_TO_REMOVE:
            app_label, codename = perm_str.split(".")
            perm = Permission.objects.filter(
                content_type__app_label=app_label,
                codename=codename,
            ).first()
            if perm is None:
                self.stdout.write(self.style.WARNING(f"Permission '{perm_str}' not found, skipping"))
                continue
            if source.permissions.filter(pk=perm.pk).exists():
                source.permissions.remove(perm)
                self.stdout.write(self.style.SUCCESS(f"Removed '{perm_str}' from '{SOURCE_ROL}'"))
            else:
                self.stdout.write(f"'{perm_str}' not in '{SOURCE_ROL}', skipping")

        clone, created = Rol.objects.get_or_create(
            name=CLONE_ROL,
            defaults={
                "description": source.description,
                "color": source.color,
            },
        )
        if not created:
            self.stdout.write(self.style.WARNING(f"'{CLONE_ROL}' already exists, updating permissions"))
            clone.permissions.clear()

        clone.permissions.set(source.permissions.all())
        self.stdout.write(self.style.SUCCESS(f"Rol '{CLONE_ROL}' {'created' if created else 'updated'} with {clone.permissions.count()} permissions"))

        orgs = source.organizationstructure_set.all()
        for org in orgs:
            org.rol.add(clone)
        self.stdout.write(self.style.SUCCESS(f"Associated '{CLONE_ROL}' to {orgs.count()} organization(s)"))

        group = Group.objects.filter(name=REGISTER_ORG_GROUP).first()
        if group is None:
            self.stdout.write(self.style.WARNING(f"Group '{REGISTER_ORG_GROUP}' not found, skipping"))
            return
        users_to_remove = User.objects.filter(groups=group).exclude(email__in=EXEMPT_EMAILS)
        count = users_to_remove.count()
        for user in users_to_remove:
            user.groups.remove(group)
        self.stdout.write(self.style.SUCCESS(f"Removed group '{REGISTER_ORG_GROUP}' from {count} user(s) (exempt: {EXEMPT_EMAILS})"))

        ligia = User.objects.filter(email=LIGIA_EMAIL).first()
        if ligia is None:
            self.stdout.write(self.style.WARNING(f"User '{LIGIA_EMAIL}' not found, skipping org cleanup"))
            return
        to_delete = UserOrganization.objects.filter(user=ligia).exclude(
            organization__name=LIGIA_EXEMPT_ORG
        )
        removed_orgs = list(to_delete.values_list("organization__name", flat=True))
        to_delete.delete()
        for org_name in removed_orgs:
            self.stdout.write(self.style.SUCCESS(f"Removed '{LIGIA_EMAIL}' from org: {org_name}"))