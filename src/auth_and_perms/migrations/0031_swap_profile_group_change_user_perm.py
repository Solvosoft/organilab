from django.db import migrations


def swap_permission(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    content_type = ContentType.objects.filter(
        app_label="auth_and_perms", model="profile"
    ).first()
    if content_type:
        Permission.objects.get_or_create(
            codename="change_own_profile",
            content_type=content_type,
            defaults={"name": "Can change own profile"},
        )

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