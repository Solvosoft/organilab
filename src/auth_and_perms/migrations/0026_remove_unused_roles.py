from django.db import migrations


def remove_unused_roles(apps, schema_editor):
    Rol = apps.get_model('auth_and_perms', 'Rol')
    # Student (ID=3), Profesor (ID=9), Administración de Organización (ID=12)
    Rol.objects.filter(pk__in=[3, 9, 12]).delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('auth_and_perms', '0025_auto_20260312_1621'),
    ]

    operations = [
        migrations.RunPython(remove_unused_roles, noop),
    ]
