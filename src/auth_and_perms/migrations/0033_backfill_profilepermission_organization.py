# -*- coding: utf-8 -*-
"""Rellena ``ProfilePermission.organization`` en las filas anteriores al campo.

El campo se añadió en 0029 como nulo y sin migración de datos, pero
``laboratory.utils.get_lab_ids()`` filtra por él. Las filas antiguas quedaron
fuera de ese filtro, así que sus usuarios ven listados vacíos en reservaciones,
reportes y laboratorio aunque conserven el rol.

La organización se deduce del propio permiso:
- permiso sobre una organización → es esa misma organización;
- permiso sobre un laboratorio → la organización a la que pertenece.

Las filas cuyo objeto ya no existe se dejan intactas: son permisos huérfanos y
su limpieza es competencia del comando ``clean_orphaned_profilepermissions``.
"""
from django.db import migrations


def backfill_organization(apps, schema_editor):
    ProfilePermission = apps.get_model("auth_and_perms", "ProfilePermission")
    Laboratory = apps.get_model("laboratory", "Laboratory")
    OrganizationStructure = apps.get_model("laboratory", "OrganizationStructure")

    org_ids = set(OrganizationStructure.objects.values_list("pk", flat=True))
    lab_orgs = dict(Laboratory.objects.values_list("pk", "organization_id"))

    updated = orphan = skipped = 0
    pending = ProfilePermission.objects.filter(
        organization__isnull=True
    ).select_related("content_type")

    for permission in pending:
        content_type = permission.content_type
        model = content_type.model if content_type else ""
        app_label = content_type.app_label if content_type else ""
        organization_id = None

        if app_label == "laboratory" and model == "organizationstructure":
            if permission.object_id in org_ids:
                organization_id = permission.object_id
            else:
                orphan += 1
        elif app_label == "laboratory" and model == "laboratory":
            if permission.object_id in lab_orgs:
                organization_id = lab_orgs[permission.object_id]
            else:
                orphan += 1
        else:
            # Permisos sobre otros modelos (p.ej. perfiles): la organización no
            # se deduce del objeto, así que se dejan como están.
            skipped += 1
            continue

        if organization_id is None:
            continue

        permission.organization_id = organization_id
        permission.save(update_fields=["organization"])
        updated += 1

    if updated or orphan or skipped:
        print(
            f"  ProfilePermission con organización asignada: {updated}"
            f" · huérfanos sin tocar: {orphan}"
            f" · fuera de la regla: {skipped}"
        )
    if orphan:
        print(
            "  Los huérfanos apuntan a objetos borrados; se limpian con"
            " 'manage.py clean_orphaned_profilepermissions --dry'"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("auth_and_perms", "0032_grant_sga_access_to_substance_roles"),
        ("laboratory", "0218_derive_laboratory_and_organization_codes"),
    ]

    operations = [
        # Irreversible por diseño: volver a dejar el campo en nulo devolvería a
        # esos usuarios a la situación de no ver sus laboratorios.
        migrations.RunPython(backfill_organization, migrations.RunPython.noop),
    ]
