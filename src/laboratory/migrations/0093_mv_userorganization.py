# Generated by Django 4.0.8 on 2023-04-04 17:56

from django.db import migrations

def mv_users(apps, schema_editor):
    OrganizationUserManagement = apps.get_model('laboratory', 'OrganizationUserManagement')
    UserOrganization = apps.get_model('laboratory', 'UserOrganization')
    for organization in OrganizationUserManagement.objects.all():
        for user in organization.users.all():
            UserOrganization.objects.create(
                organization=organization.organization,
                user=user,
                type_in_organization=1
            )


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0092_userorganization_type_in_organization'),
    ]

    operations = [
        migrations.RunPython(mv_users, reverse_code=migrations.RunPython.noop),
    ]
