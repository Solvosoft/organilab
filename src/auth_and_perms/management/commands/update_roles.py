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
    add_permissions(
        rol,
        [
            "laboratory.add_shelfobject",
        ],
    )

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
            "sga.add_provider",
            "sga.change_recipientsize",
            "sga.delete_recipientsize",
            "sga.add_substancecharacteristics",
            "sga.add_substanceobservation",
            "sga.add_substance",
            "msds.add_msdsobject",
            "sga.change_substancecharacteristics",
            "sga.add_recipientsize",
            "auth_and_perms.view_profilepermission",
            "auth_and_perms.change_profilepermission",
            "blog.add_entry",
            "blog.change_entry",
            "blog.view_entry",
            "laboratory.view_organizationstructure",
            "laboratory.view_precursorreport",
            "risk_management.view_incidentreport",
            "auth_and_perms.view_rol",
            "laboratory.view_report",
            "reservations_management.change_reservations",
            "reservations_management.change_reservedproducts",
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


def update_administrador_laboratorio():
    rol = Rol.objects.filter(name="Administrador de Laboratorio").first()
    if not rol:
        print("WARNING: Rol 'Administrador de Laboratorio' not found, skipping.")
        return
    add_permissions(
        rol,
        [
            "laboratory.can_manage_reorder",
            "laboratory.add_labororgrequest",
            "laboratory.view_labororgrequest",
            "laboratory.change_labororgrequest",
            "laboratory.delete_labororgrequest",
        ],
    )

    remove_permissions(
        rol,
        [
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
            "laboratory.can_approve_labororgrequest",
        ],
    )


def update_lectura_agregado_sustancias():
    rol = Rol.objects.filter(name="Lectura y agregado de sustancias").first()
    if not rol:
        print("WARNING: Rol 'Lectura agregado sustancias' not found, skipping.")
        return

    add_permissions(
        rol,
        [
            "laboratory.change_furniture",
            "academic.view_myprocedure",
            "laboratory.view_shelfobject",
            "laboratory.view_shelf",
        ],
    )
    remove_permissions(
        rol,
        [
            "sga.change_dangerindication",
            "sga.change_warningword",
            "sga.change_prudenceadvice",
            "sga.delete_substance",
            "sga.delete_substanceobservation",
            "sga.change_substance",
            "sga.change_substanceobservation",
            "sga.change_warningword",
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
            "laboratory.change_laboratory",
            "derb.change_customform",
            "derb.add_customform",
            "derb.delete_customform",
            "laboratory.add_catalog",
            "laboratory.change_catalog",
            "auth_and_perms.add_profilepermission",
            "academic.change_procedure",
            "academic.add_procedure",
            "academic.add_myprocedure",
            "academic.change_myprocedure",
            "academic.delete_procedure",
            "academic.add_commentprocedurestep",
            "laboratory.add_provider",
            "laboratory.change_provider",
            "laboratory.delete_provider",
            "sga.add_dangerindication",
            "sga.change_dangerindication",
            "sga.delete_dangerindication",
            "sga.add_warningword",
            "sga.change_warningword",
            "sga.delete_warningword",
            "sga.add_prudenceadvice",
            "sga.change_prudenceadvice",
            "laboratory.add_equipmenttype",
            "laboratory.change_equipmenttype",
            "laboratory.delete_equipmenttype",
            "laboratory.add_instrumentalfamily",
            "laboratory.change_instrumentalfamily",
            "laboratory.delete_instrumentalfamily",
            "laboratory.add_furniture",
            "laboratory.do_report",
            "laboratory.view_report",
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
            "laboratory.add_objectfeatures",
            "laboratory.change_objectfeatures",
            "laboratory.delete_objectfeatures",
            "laboratory.add_shelf",
            "laboratory.change_shelf",
            "laboratory.add_furniture",
            "sga.view_provider",
            "sga.add_substance",
            "sga.change_provider",
            "sga.delete_provider",
            "sga.view_displaylabel",
            "sga.add_recipientsize",
            "sga.change_recipientsize",
            "sga.delete_recipientsize",
            "sga.view_recipientsize",
            "sga.add_substancecharacteristics",
            "sga.view_substancecharacteristics",
            "sga.change_substancecharacteristics",
            "sga.view_substanceobservation",
            "sga.add_substanceobservation",
            "risk_management.view_incidentreport",
            "msds.change_msdsobject",
            "sga.view_securityleaf",
            "sga.add_provider",
            "msds.add_msdsobject",
            "laboratory.add_tranferobject",
            "laboratory.add_registeruserqr",
            "laboratory.change_registeruserqr",
            "laboratory.add_laboratory",
            "auth_and_perms.view_profilepermission",
            "auth_and_perms.add_profilepermission",
            "auth_and_perms.change_profilepermission",
            "auth_and_perms.delete_profilepermission",
            "laboratory.add_informscheduler",
            "laboratory.change_informscheduler",
            "laboratory.delete_informscheduler",
            "laboratory.add_inform",
            "laboratory.change_inform",
            "sga.view_templatesga",
            "sga.view_sgacomplement",
            "sga.view_securityleaf",
            "sga.view_substanceobservation",
            "sga.view_substance",
            "sga.view_recipientsize",
            "sga.view_label",
            "laboratory.view_registeruserqr",
            "reservations_management.view_reservations",
            "academic.change_commentprocedurestep",
            "academic.add_procedureobservations",
            "academic.add_procedurerequiredobject",
            "academic.add_procedurestep",
            "academic.change_procedurestep",
            "blog.add_entry",
            "blog.change_entry",
            "blog.view_entry",
            "djreservation.add_reservation",
            "laboratory.delete_protocol",
            "reservations_management.add_reservations",
            "reservations_management.change_reservations",
            "reservations_management.change_reservedproducts",
            "reservations_management.add_reservedproducts",
            "reservations_management.add_reservations",
        ],
    )
    remove_permissions(
        rol,
        [
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
        ],
    )


def update_asistente_laboratorio():
    rol = Rol.objects.filter(name="Asistente de laboratorio").first()
    if not rol:
        print("WARNING: Rol 'Asistente de laboratorio' not found, skipping.")
        return
    add_permissions(
        rol,
        [
            "laboratory.can_manage_reorder",
        ],
    )

    remove_permissions(
        rol,
        [
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
        ],
    )


def update_profesor():
    rol = Rol.objects.filter(name="Profesor").first()
    if not rol:
        print("WARNING: Rol 'Profesor' not found, skipping.")
        return

    add_permissions(
        rol,
        [
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
        ],
    )

    remove_permissions(
        rol,
        [
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
        ],
    )


def update_tesista_modulo_desechos():
    rol = Rol.objects.filter(name="Tesista modulo desechos").first()
    if not rol:
        print("WARNING: Rol 'Tesista Modulo de Sechos' not found, skipping.")
        return

    add_permissions(
        rol,
        [
            "laboratory.change_shelfobject",
            "laboratory.view_shelf",
            "laboratory.view_catalog",
            "risk_management.view_riskzone",
        ],
    )

    remove_permissions(
        rol,
        [
            "laboratory.add_shelf",
            "laboratory.change_shelf",
            "laboratory.delete_shelf",
            "laboratory.add_furniture",
            "laboratory.change_furniture",
            "laboratory.delete_furniture",
            "laboratory.add_laboratory",
            "laboratory.change_laboratory",
            "laboratory.delete_laboratory",
            "laboratory.add_laboratoryroom",
            "laboratory.change_laboratoryroom",
            "laboratory.delete_laboratoryroom",
            "laboratory.delete_shelfobject",
            "laboratory.add_object",
            "laboratory.change_object",
            "laboratory.delete_object",
            "laboratory.add_catalog",
            "laboratory.change_catalog",
            "laboratory.delete_catalog",
            "laboratory.add_equipmenttype",
            "laboratory.change_equipmenttype",
            "laboratory.delete_equipmenttype",
            "laboratory.add_instrumentalfamily",
            "laboratory.change_instrumentalfamily",
            "laboratory.delete_instrumentalfamily",
            "sga.add_dangerindication",
            "sga.change_dangerindication",
            "sga.delete_dangerindication",
            "sga.add_warningword",
            "sga.change_warningword",
            "sga.delete_warningword",
            "sga.add_prudenceadvice",
            "sga.change_prudenceadvice",
            "sga.delete_prudenceadvice",
            "sga.add_substance",
            "sga.change_substance",
            "sga.add_recipientsize",
            "sga.change_recipientsize",
            "sga.delete_recipientsize",
            "sga.add_substancecharacteristics",
            "sga.change_substancecharacteristics",
            "sga.add_substanceobservation",
            "sga.change_substanceobservation",
            "sga.delete_substanceobservation",
            "sga.delete_displaylabel",
            "sga.change_displaylabel",
            "sga.add_displaylabel",
            "sga.add_label",
            "sga.change_label",
            "sga.delete_label",
            "sga.add_provider",
            "sga.change_provider",
            "sga.delete_provider",
            "sga.add_templatesga",
            "sga.change_templatesga",
            "sga.delete_templatesga",
            "sga.view_displaylabel",
            "risk_management.add_riskzone",
            "risk_management.change_riskzone",
            "risk_management.delete_riskzone",
            "risk_management.add_zonetype",
            "risk_management.add_incidentreport",
            "risk_management.change_incidentreport",
            "risk_management.delete_incidentreport",
            "risk_management.add_regent",
            "risk_management.change_regent",
            "risk_management.delete_regent",
            "risk_management.add_buildings",
            "risk_management.change_buildings",
            "risk_management.delete_buildings",
            "risk_management.add_structure",
            "risk_management.change_structure",
            "risk_management.delete_structure",
            "auth_and_perms.add_profilepermission",
            "auth_and_perms.change_profilepermission",
            "auth_and_perms.delete_profilepermission",
            "reservations_management.view_reservations",
            "reservations_management.add_reservations",
            "reservations_management.change_reservations",
            "reservations_management.delete_reservations",
            "reservations_management.add_reservedproducts",
            "reservations_management.change_reservedproducts",
            "reservations_management.delete_reservedproducts",
            "msds.add_msdsobject",
            "msds.change_msdsobject",
            "msds.delete_msdsobject",
            "laboratory.add_tranferobject",
            "laboratory.change_tranferobject",
            "laboratory.delete_tranferobject",
            "laboratory.add_registeruserqr",
            "laboratory.change_registeruserqr",
            "laboratory.add_laboratory",
            "laboratory.change_laboratory",
            "laboratory.delete_laboratory",
            "laboratory.add_informscheduler",
            "laboratory.change_informscheduler",
            "laboratory.delete_informscheduler",
            "laboratory.add_inform",
            "laboratory.change_inform",
            "sga.view_substance",
            "sga.view_substancecharacteristics",
            "sga.view_substanceobservation",
            "sga.change_sgacomplement",
            "sga.view_sgacomplement",
            "sga.view_recipientsize",
            "sga.delete_substance",
            "sga.view_templatesga",
            "sga.change_securityleaf",
            "sga.view_label",
            "sga.view_provider",
            "sga.view_securityleaf",
            "laboratory.delete_provider",
            "laboratory.change_provider",
            "laboratory.delete_protocol",
            "laboratory.view_precursorreport",
            "laboratory.view_organizationstructurerelations",
            "laboratory.delete_organizationstructure",
            "laboratory.add_organizationstructurerelations",
            "laboratory.change_organizationstructure",
            "laboratory.add_organizationstructure",
            "laboratory.delete_objectfeatures",
            "laboratory.change_objectfeatures",
            "laboratory.do_report",
            "laboratory.delete_inform",
            "derb.add_customform",
            "derb.change_customform",
            "derb.delete_customform",
            "auth_and_perms.view_profilepermission",
            "auth_and_perms.add_profile",
            "auth_and_perms.add_rol",
            "auth_and_perms.change_rol",
            "auth.add_user",
            "blog.add_entry",
            "blog.change_entry",
            "blog.view_entry",
            "blog.delete_entry",
            "blog.add_category",
            "djgentelella.can_manage_permissions",
            "academic.add_commentprocedurestep",
            "academic.delete_procedure",
            "academic.delete_procedureobservations",
            "academic.delete_procedurerequiredobject",
            "academic.change_procedurestep",
            "academic.change_commentprocedurestep",
            "academic.add_myprocedure",
            "academic.add_procedure",
            "academic.delete_procedurestep",
            "academic.add_procedurestep",
            "academic.add_procedurerequiredobject",
            "academic.add_procedureobservations",
            "academic.change_procedure",
            "academic.change_myprocedure",
            "academic.delete_commentprocedurestep",
            "laboratory.view_organizationstructure",
            "laboratory.view_report",
            "djreservation.add_reservation",
        ],
    )


def update_solo_lectura():
    rol = Rol.objects.filter(name="Solo Lectura").first()
    if not rol:
        print("WARNING: Rol 'Solo Lectura' not found, skipping.")
        return

    add_permissions(
        rol,
        [
            "laboratory.view_laboratoryroom",
            "laboratory.view_shelf",
            "laboratory.view_furniture",
            "laboratory.view_provider",
            "academic.view_procedure",
            "laboratory.view_inform",
            "risk_management.view_buildings",
            "laboratory.view_sustancecharacteristics",
            "risk_management.view_structure",
            "laboratory.view_object",
            "laboratory.view_laboratoryprocess",
            "laboratory.view_shelfobjectobservation",
            "risk_management.view_riskzone",
            "risk_management.view_regent",
            "risk_management.view_workday",
            "reservations_management.view_reservations",
        ],
    )

    remove_permissions(
        rol,
        [
            "laboratory.change_object",
            "laboratory.add_catalog",
            "laboratory.change_catalog",
            "laboratory.change_equipmenttype",
            "laboratory.change_objectfeatures",
            "laboratory.view_registeruserqr",
            "sga.add_dangerindication",
            "sga.add_warningword",
            "risk_management.add_incidentreport",
            "derb.add_customform",
            "academic.add_commentprocedurestep",
            "academic.change_commentprocedurestep",
            "academic.delete_commentprocedurestep",
            "academic.change_myprocedure",
            "blog.change_entry",
            "djreservation.add_reservation",
            "laboratory.add_registeruserqr",
            "laboratory.change_furniture",
            "laboratory.change_laboratory",
            "laboratory.change_laboratoryroom",
            "laboratory.change_shelf",
            "laboratory.change_shelfobjectlog",
            "reservations_management.add_reservations",
            "reservations_management.add_reservedproducts",
            "reservations_management.change_reservations",
            "risk_management.add_zonetype",
            "risk_management.change_incidentreport",
            "sga.add_substanceobservation",
            "sga.change_recipientsize",
            "laboratory.do_report",
            "laboratory.view_report",
            "laboratory.view_organizationstructure",
            "laboratory.view_organizationstructurerelations",
            "laboratory.add_registeruserqr",
            "auth_and_perms.view_profilepermission",
            "blog.add_entry",
            "blog.change_entry",
            "blog.view_entry",
        ],
    )


def update_tecnico_laboratorio():
    rol = Rol.objects.filter(name="Técnico de Laboratorio").first()
    if not rol:
        print("WARNING: Rol 'Tecnico Laboratorio' not found, skipping.")
        return

    add_permissions(
        rol,
        [
            "laboratory.add_commentinform",
            "laboratory.view_commentinform",
            "laboratory.delete_commentinform",
            "laboratory.change_commentinform",
            "laboratory.view_catalog",
            "reservations_management.delete_reservations",
            "risk_management.view_buildings",
            "risk_management.view_structure",
            "risk_management.view_regent",
            "risk_management.view_workday",
        ],
    )

    remove_permissions(
        rol,
        [
            "auth.add_user",
            "auth_and_perms.add_profile",
            "auth_and_perms.add_profilepermission",
            "auth_and_perms.change_profilepermission",
            "auth_and_perms.delete_profilepermission",
            "auth_and_perms.change_rol",
            "auth_and_perms.add_rol",
            "auth_and_perms.view_profilepermission",
            "auth_and_perms.view_rol",
            "derb.delete_customform",
            "djgentelella.can_manage_permissions",
            "laboratory.add_clinventory",
            "laboratory.change_clinventory",
            "laboratory.delete_clinventory",
            "laboratory.view_clinventory",
            "laboratory.change_laboratory",
            "laboratory.delete_laboratory",
            "laboratory.add_laboratory",
            "laboratory.add_informscheduler",
            "laboratory.do_report",
            "laboratory.view_report",
            "laboratory.delete_laboratoryroom",
            "laboratory.change_object",
            "laboratory.delete_object",
            "laboratory.change_objectfeatures",
            "laboratory.delete_objectfeatures",
            "laboratory.add_organizationstructure",
            "laboratory.change_organizationstructure",
            "laboratory.delete_organizationstructure",
            "laboratory.view_organizationstructure",
            "laboratory.add_organizationstructurerelations",
            "laboratory.delete_registeruserqr",
            "laboratory.change_registeruserqr",
            "laboratory.delete_shelf",
            "laboratory.delete_sustancecharacteristics",
            "msds.add_msdsobject",
            "msds.change_msdsobject",
            "msds.delete_msdsobject",
            "risk_management.change_incidentreport",
            "risk_management.add_incidentreport",
            "risk_management.delete_incidentreport",
            "risk_management.add_riskzone",
            "risk_management.change_riskzone",
            "risk_management.delete_riskzone",
            "risk_management.add_zonetype",
            "sga.add_dangerindication",
            "sga.change_dangerindication",
            "sga.delete_dangerindication",
            "sga.add_displaylabel",
            "sga.change_displaylabel",
            "sga.delete_displaylabel",
            "sga.add_label",
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
            "sga.delete_substanceobservation",
            "sga.add_templatesga",
            "sga.add_warningword",
            "sga.change_warningword",
            "sga.delete_warningword",
            "sga.change_dangerindication",
            "sga.delete_dangerindication",
            "sga.delete_prudenceadvice",
            "sga.delete_dangerprudence",
            "sga.change_dangersubstance",
            "sga.delete_dangersubstance",
            "sga.change_dangersubstancecategory",
            "sga.delete_dangersubstancecategory",
            "sga.delete_hcodecategory",
            "sga.delete_pictogram",
            "sga.delete_warningword",
            "sga.delete_warningclass",
            "sga.add_recipientsize",
            "sga.change_recipientsize",
            "sga.delete_recipientsize",
            "sga.view_recipientsize",
            "sga.change_templatesga",
            "sga.view_builderinformation",
            "sga.view_substance",
            "sga.change_substance",
            "auth_and_perms.institution_can_access",
        ],
    )


def update_sga():
    rol = Rol.objects.filter(name="SGA").first()
    if not rol:
        print("WARNING: Rol 'SGA' not found, skipping.")
        return

    remove_permissions(
        rol,
        [
            "sga.change_dangerindication",
            "sga.delete_dangerindication",
            "sga.delete_prudenceadvice",
            "sga.delete_dangerprudence",
            "sga.change_dangersubstance",
            "sga.delete_dangersubstance",
            "sga.change_dangersubstancecategory",
            "sga.delete_dangersubstancecategory",
            "sga.delete_hcodecategory",
            "sga.delete_pictogram",
            "sga.delete_warningword",
            "sga.delete_warningclass",
            "sga.add_recipientsize",
            "sga.change_recipientsize",
            "sga.delete_recipientsize",
            "sga.view_recipientsize",
            "sga.change_templatesga",
            "sga.view_builderinformation",
            "sga.view_substance",
            "sga.change_substance",
            "auth_and_perms.institution_can_access",
        ],
    )


def update_regente():
    rol = Rol.objects.filter(name="Regente").first()
    if not rol:
        print("WARNING: Rol 'Regente' not found, skipping.")
        return
    add_permissions(
        rol,
        [
            "auth.view_user",
            "risk_management.view_workday",
            "laboratory.view_provider",
            "laboratory.view_protocol",
        ],
    )
    remove_permissions(
        rol,
        [
            "laboratory.view_baseunitvalues",
            "laboratory.view_blockedlistnotification",
            "laboratory.view_clinventory",
            "msds.view_organilabnode",
            "sga.view_builderinformation",
        ],
    )


def update_administrador_superior():
    rol = Rol.objects.filter(name="Administrativo superior").first()
    if not rol:
        print("WARNING: Rol 'Administrativo superior' not found, skipping.")
        return
    add_permissions(
        rol,
        [
            "laboratory.can_manage_reorder",
            "laboratory.add_labororgrequest",
            "laboratory.view_labororgrequest",
            "laboratory.change_labororgrequest",
            "laboratory.delete_labororgrequest",
            "laboratory.can_approve_labororgrequest",
        ],
    )


def update_centro_trabajo():
    rol = Rol.objects.filter(name="Administración de centro de trabajo").first()
    if not rol:
        print("WARNING: Rol 'Centro de trabajo' not found, skipping.")
        return

    remove_permissions(
        rol,
        [
            "sga.add_dangerindication",
            "sga.change_dangerindication",
            "sga.delete_dangerindication",
            "sga.add_warningword",
            "sga.change_warningword",
            "sga.delete_warningword",
            "sga.add_prudenceadvice",
            "sga.change_prudenceadvice",
            "sga.delete_prudenceadvice",
            "sga.add_substance",
            "sga.change_substance",
            "sga.delete_substance",
            "sga.add_substancecharacteristics",
            "sga.change_substancecharacteristics",
            "sga.add_substanceobservation",
            "sga.change_substanceobservation",
            "sga.delete_substanceobservation",
            "sga.add_templatesga",
            "sga.view_recipientsize",
            "sga.change_recipientsize",
            "msds.add_msdsobject",
            "msds.change_msdsobject",
            "auth_and_perms.add_profilepermission",
            "auth_and_perms.change_profilepermission",
            "auth_and_perms.delete_profilepermission",
            "auth_and_perms.add_profile",
            "auth_and_perms.change_profile",
            "auth_and_perms.delete_profile",
            "laboratory.add_clinventory",
            "laboratory.change_clinventory",
            "laboratory.delete_clinventory",
            "laboratory.view_clinventory",
            "laboratory.delete_laboratory",
            "laboratory.change_object",
            "laboratory.delete_object",
            "risk_management.delete_riskzone",
            "risk_management.delete_buildings",
            "risk_management.delete_structure",
            "risk_management.delete_regent",
            "laboratory.delete_objectfeatures",
            "auth_and_perms.change_rol",
            "auth_and_perms.add_rol",
            "auth_and_perms.view_profilepermission",
            "blog.delete_entry",
            "blog.change_entry",
            "blog.add_entry",
            "blog.view_entry",
            "djgentelella.can_manage_permissions",
            "laboratory.change_catalog",
            "laboratory.delete_catalog",
            "laboratory.change_equipmenttype",
            "laboratory.delete_equipmenttype",
            "blog.add_category",
            "laboratory.change_objectfeatures",
        ],
    )
    add_permissions(
        rol,
        [
            "laboratory.add_informscheduler",
            "laboratory.view_informscheduler",
            "laboratory.change_informscheduler",
            "laboratory.can_manage_reorder",
        ],
    )


class Command(BaseCommand):
    help = "Update rol permissions by segment — idempotent, safe to re-run"

    def handle(self, *args, **options):
        update_sga()
        update_estudiante()
        update_administrador_laboratorio()
        update_asistente_laboratorio()
        update_profesor()
        update_lectura_agregado_sustancias()
        update_creador_laboratorios()
        update_tesista_modulo_desechos()
        update_depositante_residuos()
        update_solo_lectura()
        update_regente()
        update_tecnico_laboratorio()
        update_centro_trabajo()
        update_administrador_superior()
