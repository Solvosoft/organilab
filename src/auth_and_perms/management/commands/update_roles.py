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
        "djgentelella.can_manage_permissions",
        "auth_and_perms.delete_profilepermission",
    ])

def update_asistente_laboratorio():
    rol = Rol.objects.filter(name="Asistente de laboratorio").first()
    if not rol:
        print("WARNING: Rol 'Asistente de laboratorio' not found, skipping.")
        return

    remove_permissions(rol, [
        "laboratory.delete_laboratory",
        "sga.add_dangerindication",
        "sga.change_dangerindication",
        "sga.delete_dangerindication",
        "sga.view_dangerindication",
        "sga.add_displaylabel",
        "sga.change_displaylabel",
        "sga.delete_displaylabel",
        "sga.view_displaylabel",
        "sga.add_label",
        "sga.view_label",
        "sga.add_provider",
        "sga.view_provider",
        "sga.add_prudenceadvice",
        "sga.change_prudenceadvice",
        "sga.delete_prudenceadvice",
        "sga.view_prudenceadvice",
        "sga.add_recipientsize",
        "sga.change_recipientsize",
        "sga.delete_recipientsize",
        "sga.view_recipientsize",
        "sga.change_securityleaf",
        "sga.view_securityleaf",
        "sga.add_sgacomplement",
        "sga.change_sgacomplement",
        "sga.view_sgacomplement",
        "sga.add_substance",
        "sga.change_substance",
        "sga.delete_substance",
        "sga.view_substance",
        "sga.add_substancecharacteristics",
        "sga.change_substancecharacteristics",
        "sga.view_substancecharacteristics",
        "sga.add_substanceobservation",
        "sga.change_substanceobservation",
        "sga.delete_substanceobservation",
        "sga.view_substanceobservation",
        "sga.add_templatesga",
        "sga.change_templatesga",
        "sga.view_templatesga",
        "sga.add_warningword",
        "sga.change_warningword",
        "sga.view_warningword",
        "msds.add_msdsobject",
        "msds.change_msdsobject",
        "msds.delete_msdsobject",
        "risk_management.add_incidentreport",
        "risk_management.change_incidentreport",
        "risk_management.delete_incidentreport",
        "risk_management.add_riskzone",
        "risk_management.change_riskzone",
        "risk_management.delete_riskzone",
        "risk_management.add_zonetype",
        "djgentelella.can_manage_permissions",
        "auth_and_perms.delete_profilepermission",
    ])

def update_profesor():
    rol = Rol.objects.filter(name="Profesor").first()
    if not rol:
        print("WARNING: Rol 'Profesor' not found, skipping.")
        return

    add_permissions(rol, [
        "laboratory.view_catalog",
        "laboratory.view_equipmenttype",
        "laboratory.view_furniture",
        "laboratory.view_laboratory",
        "laboratory.view_laboratoryroom",
        "laboratory.view_object",
        "laboratory.view_objectfeatures",
        "laboratory.view_protocol",
        "laboratory.view_provider",
        "laboratory.can_view_disposal",
        "laboratory.view_shelf",
        "laboratory.view_shelfobject",
        "laboratory.view_shelfobjectcalibrate",
        "laboratory.view_shelfobjectguarantee",
        "laboratory.view_shelfobjectlog",
        "laboratory.view_shelfobjecttraining",

        "academic.add_myprocedure",
        "academic.view_myprocedure",
        "academic.change_myprocedure",
        "academic.delete_myprocedure",
    ])

    remove_permissions(rol, [
        "laboratory.view_precursorreport",
        "laboratory.view_organizationstructure",
        "laboratory.view_organizationstructurerelations",
        "laboratory.view_report",
        "laboratory.view_commentinform",
        "laboratory.can_view_contract",
        "laboratory.view_registeruserqr",

        "academic.add_procedure",
        "academic.change_procedure",
        "academic.delete_procedure",
        "academic.view_procedure",
    ])


class Command(BaseCommand):
    help = "Update rol permissions by segment — idempotent, safe to re-run"

    def handle(self, *args, **options):
        update_estudiante()
        update_administrador_laboratorio()
        update_asistente_laboratorio()
        update_profesor()
