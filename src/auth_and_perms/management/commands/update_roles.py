from django.contrib.auth.models import Permission
from django.core.management import BaseCommand

from auth_and_perms.models import Rol


def add_permissions(rol, perms):
    for perm_str in perms:
        app_label, codename = perm_str.split(".")
        perm = Permission.objects.filter(
            content_type__app_label=app_label, codename=codename
        ).first()
        if perm:
            rol.permissions.add(perm)
        else:
            print(f"WARNING: permission '{perm_str}' not found, skipping.")


def remove_permissions(rol, perms):
    for perm_str in perms:
        app_label, codename = perm_str.split(".")
        perm = Permission.objects.filter(
            content_type__app_label=app_label, codename=codename
        ).first()
        if perm:
            rol.permissions.remove(perm)


def update_estudiante():
    rol = Rol.objects.filter(name="Estudiante").first()
    if not rol:
        print("WARNING: Rol 'Estudiante' not found, skipping.")
        return
    add_permissions(rol, [
        "laboratory.view_catalog",
        "laboratory.change_shelfobjectlog",
        "laboratory.view_shelf",
        "laboratory.view_provider",
    ])


class Command(BaseCommand):
    help = "Update rol permissions by segment — idempotent, safe to re-run"

    def handle(self, *args, **options):
        update_estudiante()
