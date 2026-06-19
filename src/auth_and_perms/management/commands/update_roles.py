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
    add_permissions(
        rol,
        [
            "laboratory.view_catalog",
            "laboratory.change_shelfobjectlog",
            "laboratory.view_shelf",
            "laboratory.view_provider",
        ],
    )


def update_depositante_residuos():
    rol = Rol.objects.filter(name="Depositante de residuos").first()
    if not rol:
        print("WARNING: Rol 'Depositante de residuos' not found, skipping.")
        return
    remove_permissions(
        rol,
        [
            "sga.add_dangerindication",
            "sga.add_warningword",
            "sga.add_prudenceadvice",
            "sga.add_observation",
            "sga.update_dangerindication",
            "sga.update_warningword",
            "sga.update_prudenceadvice",
            "sga.delete_substance",
            "sga.delete_substanceobservation",
            "sga.change_substance",
            "sga.change_substanceobservation",
            "sga.change_warningword",
            "sga.change_prudenceadvice",
            "sga.change_dangerindication",
            "sga.view_substance",
            "sga.view_dangerindication",
            "sga.view_warningword",
            "sga.view_prudenceadvice",
            "sga.view_substanceobservation",
            "sga.view_recipientsize",
            "laboratory.do_report",
            "laboratory.change_protocol",
            "laboratory.add_protocol",
            "laboratory.change_laboratoryprocess",
            "laboratory.add_laboratoryprocess",
            "laboratory.change_objectfeatures",
            "laboratory.add_objectfeatures",
            "laboratory.add_object",
            "laboratory.change_object",
            "laboratory.change_laboratory",
            "laboratory.change_laboratoryroom",
            "laboratory.add_laboratoryroom",
            "laboratory.view_inform",
            "laboratory.view_laboratoryprocess",
            "laboratory.change_inform",
            "laboratory.add_informscheduler",
            "laboratory.change_furniture",
            "laboratory.can_manage_inform_status",
            "laboratory.change_catalog",
            "auth_and_perms.add_profilepermission",
            "academic.view_procedure",
            "academic.change_procedure",
            "academic.add_procedure",
            "academic.view_myprocedure",
            "academic.add_myprocedure",
            "academic.change_myprocedure",
            "academic.delete_procedure",
            "academic.add_commentprocedurestep",
            "academic.change_commentprocedurestep",
            "academic.delete_commentprocedurestep",
            "laboratory.add_provider",
            "laboratory.change_provider",
            "laboratory.delete_provider",
            "laboratory.change_shelf",
            "laboratory.add_shelf",
            "laboratory.change_furniture",
            "laboratory.add_furniture",
            "risk_management.add_incidentreport",
            "risk_management.change_incidentreport",
            "risk_management.delete_incidentreport",
            "risk_management.add_zonetype",
            "risk_management.change_zonetype",
            "risk_management.delete_zonetype",
            "risk_management.add_regent",
            "risk_management.change_regent",
            "risk_management.delete_regent",
            "risk_management.add_buildings",
            "risk_management.change_buildings",
            "risk_management.delete_buildings",
            "risk_management.add_structure",
            "risk_management.change_structure",
            "risk_management.delete_structure",
            "risk_management.view_riskzone",
            "sga.add_dangerindication",
            "sga.change_dangerindication",
            "sga.delete_dangerindication",
            "sga.add_warningword",
            "sga.change_warningword",
            "sga.delete_warningword",
            "msds.add_msdsobject",
            "msds.change_msdsobject",
            "msds.delete_msdsobject",
        ],
    )


def update_creador_laboratorios():
    rol = Rol.objects.filter(name="Creador de laboratorio").first()
    if not rol:
        print("WARNING: Rol 'Creador de laboratorio' not found, skipping.")
        return
    add_permissions(
        rol,
        [
            "laboratory.add_shelf",
            "laboratory.add_furniture",
            "laboratory.add_laboratory",
            "laboratory.change_shelf",
            "laboratory.change_furniture",
            "laboratory.view_equipmentcharacteristics",
            "laboratory.view_instrumentalfamily",
            "laboratory.view_equipmenttype",
            "laboratory.add_shelf",
            "laboratory.view_catalog",
            "laboratory.view_provider",
            "laboratory.add_provider",
            "laboratory.change_provider",
            "laboratory.view_protocol",
            "laboratory.add_protocol",
            "laboratory.change_protocol",
            "laboratory.view_laboratoryprocess",
            "laboratory.add_laboratoryprocess",
            "laboratory.change_laboratoryprocess",
            "laboratory.view_inform",
            "laboratory.add_inform",
            "laboratory.change_inform",
        ],
    )
    remove_permissions(
        rol,
        [
            "laboratory.change_object",
            "laboratory.delete_shelf",
            "laboratory.delete_furniture",
            "laboratory.delete_laboratory",
            "laboratory.delete_object",
            "laboratory.add_object",
            "laboratory.delete_laboratoryroom",
            "laboratory.change_objectfeatures",
        ],
    )


class Command(BaseCommand):
    help = "Update rol permissions by segment — idempotent, safe to re-run"

    def handle(self, *args, **options):
        # update_estudiante()
        # update_depositante_residuos()
        update_creador_laboratorios()
