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

def update_administrador_laboratorio():
    rol = Rol.objects.filter(name="Administrador de Laboratorio").first()
    if not rol:
        print("WARNING: Rol 'Administrador de Laboratorio' not found, skipping.")
        return

    remove_permissions(rol, [
        "laboratory.delete_laboratory",
        "sga.add_displaylabel",
        "sga.change_displaylabel",
        "sga.add_label",
        "sga.add_provider",
        "sga.add_prudenceadvice",
        "sga.change_prudenceadvice",
        "sga.delete_prudenceadvice",
        "sga.add_recipientsize",
        "sga.change_recipientsize",
        "sga.delete_recipientsize",
        "sga.change_securityleaf",
        "sga.add_substance",
        "sga.change_substance",
        "sga.delete_substance",
        "sga.add_substancecharacteristics",
        "sga.change_substancecharacteristics",
        "sga.add_substanceobservation",
        "sga.change_substanceobservation",
        "sga.add_templatesga",
        "sga.add_warningword",
        "sga.change_warningword",
        "sga.delete_warningword",
        "sga.add_dangerindication",
        "sga.change_dangerindication",
        "msds.delete_msdsobject",
        "msds.add_msdsobject",
        "msds.change_msdsobject",
    ])


class Command(BaseCommand):
    help = "Update rol permissions by segment — idempotent, safe to re-run"

    def handle(self, *args, **options):
        update_estudiante()
        update_administrador_laboratorio()
