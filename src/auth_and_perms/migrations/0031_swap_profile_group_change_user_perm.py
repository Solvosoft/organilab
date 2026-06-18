from django.contrib.auth.management import create_permissions
from django.db import migrations


def swap_permission(apps, schema_editor):
    # The Meta.permissions entry added in the previous migration is only
    # materialized into the auth_permission table by the post_migrate
    # signal, which fires after this whole `migrate` run finishes. Force
    # it now so the lookup below doesn't silently no-op on a fresh install.
    create_permissions(apps.get_app_config("auth_and_perms"), verbosity=0)

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    group = Group.objects.filter(name="Profile").first()
    if not group:
        return

    old_perm = Permission.objects.filter(
        content_type__app_label="auth", codename="change_user"
    ).first()
    if old_perm:
        group.permissions.remove(old_perm)

    new_perm = Permission.objects.filter(
        content_type__app_label="auth_and_perms", codename="change_own_profile"
    ).first()
    if new_perm:
        group.permissions.add(new_perm)


def revert_permission(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    group = Group.objects.filter(name="Profile").first()
    if not group:
        return

    new_perm = Permission.objects.filter(
        content_type__app_label="auth_and_perms", codename="change_own_profile"
    ).first()
    if new_perm:
        group.permissions.remove(new_perm)

    old_perm = Permission.objects.filter(
        content_type__app_label="auth", codename="change_user"
    ).first()
    if old_perm:
        group.permissions.add(old_perm)


class Migration(migrations.Migration):

    dependencies = [
        ("auth_and_perms", "0030_add_change_own_profile_permission"),
    ]

    operations = [
        migrations.RunPython(swap_permission, revert_permission),
    ]