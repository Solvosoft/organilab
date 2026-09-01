from django.db import migrations

ACTIONS = ("add", "change", "delete", "view")

LEGACY = "sustancecharacteristics"  # laboratory (sin «b»)
TARGET = "substancecharacteristics"  # sga


def _permission_maps(apps, db_alias):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")

    legacy_ct = (
        ContentType.objects.using(db_alias)
        .filter(app_label="laboratory", model=LEGACY)
        .first()
    )
    target_ct = (
        ContentType.objects.using(db_alias)
        .filter(app_label="sga", model=TARGET)
        .first()
    )
    if not legacy_ct or not target_ct:
        return {}, {}

    legacy = {
        p.codename: p.pk
        for p in Permission.objects.using(db_alias).filter(content_type=legacy_ct)
    }
    target = {
        p.codename: p.pk
        for p in Permission.objects.using(db_alias).filter(content_type=target_ct)
    }
    return legacy, target


def grant_sga_equivalents(apps, schema_editor):
    """Da a cada rol y grupo el permiso SGA equivalente al que ya tenía en laboratory.

    Las características se migraron a sga.SubstanceCharacteristics, pero los
    permisos son de otro modelo y no viajan solos: un rol con
    `laboratory.change_sustancecharacteristics` se quedaría sin poder editar
    nada. Aquí se completa la equivalencia sin quitar nada, para que revocar los
    permisos antiguos siga siendo una decisión aparte.
    """
    db_alias = schema_editor.connection.alias
    Rol = apps.get_model("auth_and_perms", "Rol")
    Group = apps.get_model("auth", "Group")

    legacy, target = _permission_maps(apps, db_alias)
    if not legacy or not target:
        return

    pairs = [
        (legacy["%s_%s" % (action, LEGACY)], target["%s_%s" % (action, TARGET)])
        for action in ACTIONS
        if "%s_%s" % (action, LEGACY) in legacy
        and "%s_%s" % (action, TARGET) in target
    ]

    granted = 0
    for model in (Rol, Group):
        for holder in model.objects.using(db_alias).all():
            held = set(holder.permissions.values_list("pk", flat=True))
            missing = [new for old, new in pairs if old in held and new not in held]
            if missing:
                holder.permissions.add(*missing)
                granted += len(missing)

    if granted:
        print(f"\nGranted {granted} equivalent SGA permissions")


def revoke_sga_equivalents(apps, schema_editor):
    """No se revoca nada al revertir.

    Los permisos SGA también se conceden por otras vías (roles nuevos, el propio
    catálogo de urlname_permissions), así que quitarlos aquí retiraría accesos
    legítimos que esta migración no otorgó.
    """


class Migration(migrations.Migration):

    dependencies = [
        ("laboratory", "0213_sdstraceability_require_sga_fk"),
        ("auth_and_perms", "0031_swap_profile_group_change_user_perm"),
        ("sga", "0089_substancecharacteristics_img_representation"),
    ]

    operations = [
        migrations.RunPython(grant_sga_equivalents, reverse_code=revoke_sga_equivalents),
    ]
