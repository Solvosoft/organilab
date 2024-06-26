# Generated by Django 4.1.10 on 2024-03-14 22:14

from django.db import migrations

def create_provider_laboratory(apps, schema_editor):
    Provider = apps.get_model('laboratory', 'Provider')
    Provider.objects.create(name="No se dispone de proveedor", phone_number="61569029",
                            email="contacto@organilab.org")
def delete_provider_laboratory(apps, schema_editor):
    Provider = apps.get_model('laboratory', 'Provider')
    Provider.objects.filter(laboratory__isnull=True).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0135_equipmenttype_alter_shelfobject_options_and_more'),
    ]

    operations = [
        migrations.RunPython(create_provider_laboratory,
                             reverse_code=delete_provider_laboratory)
    ]







