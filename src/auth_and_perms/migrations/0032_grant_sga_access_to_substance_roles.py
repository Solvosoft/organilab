from django.db import migrations

GATE = "institution_can_access"
SUBSTANCE_PERM = "change_substance"


def _gate_permission(Permission):
    return Permission.objects.filter(
        content_type__app_label="auth_and_perms", codename=GATE
    ).first()


def grant_sga_gate(apps, schema_editor):
    """Da acceso al módulo SGA a los roles que gestionan sustancias.

    `auth_and_perms.institution_can_access` es la puerta de entrada al módulo:
    todas las vistas del asistente la exigen además del permiso concreto de cada
    paso. Concederla solo por un rol específico deja fuera a quienes tienen los
    permisos de sustancias por otros roles, que entonces pueden cambiarlas sobre
    el papel pero no alcanzan ninguna pantalla donde hacerlo.

    El criterio es esa misma coherencia: quien puede cambiar sustancias
    (`sga.change_substance`) debe poder entrar al módulo donde se gestionan. No
    se retira a nadie ni se añade ningún otro permiso, y fuera de SGA esta puerta
    solo abre el tutorial y el formulario de comentarios, así que el alcance se
    limita al módulo.
    """
    Rol = apps.get_model("auth_and_perms", "Rol")
    Permission = apps.get_model("auth", "Permission")

    gate = _gate_permission(Permission)
    if gate is None:
        # En una base recién creada los permisos los genera `post_migrate`, que
        # corre después de las migraciones: no hay nada que conceder todavía.
        return

    roles = Rol.objects.filter(
        permissions__content_type__app_label="sga",
        permissions__codename=SUBSTANCE_PERM,
    ).distinct()

    granted = []
    for rol in roles:
        if not rol.permissions.filter(pk=gate.pk).exists():
            rol.permissions.add(gate)
            granted.append(rol.name)

    if granted:
        print(f"\nGranted SGA access to {len(granted)} roles: {', '.join(granted)}")


def revoke_sga_gate(apps, schema_editor):
    """Deja el permiso solo donde estaba: en el rol «SGA».

    Se quita de los roles a los que esta migración se lo dio, reconociéndolos por
    la misma regla, y se respeta «SGA» porque ya lo tenía de antes.
    """
    Rol = apps.get_model("auth_and_perms", "Rol")
    Permission = apps.get_model("auth", "Permission")

    gate = _gate_permission(Permission)
    if gate is None:
        return

    roles = (
        Rol.objects.filter(
            permissions__content_type__app_label="sga",
            permissions__codename=SUBSTANCE_PERM,
        )
        .exclude(name="SGA")
        .distinct()
    )
    for rol in roles:
        rol.permissions.remove(gate)


class Migration(migrations.Migration):
    """Sin esto el módulo SGA es inalcanzable para cualquier usuario real."""

    dependencies = [
        ("auth_and_perms", "0031_swap_profile_group_change_user_perm"),
        # El permiso `sga.change_substance` que define la regla debe existir ya.
        ("sga", "0093_substance_laboratories"),
    ]

    operations = [
        migrations.RunPython(grant_sga_gate, reverse_code=revoke_sga_gate),
    ]
