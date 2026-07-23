from django.db import migrations


def fix_salas_muebles_url(apps, schema_editor):
    Tutorial = apps.get_model('presentation', 'Tutorial')
    Tutorial.objects.filter(slug='salas-muebles').update(
        url_name='laboratory:rooms_create'
    )


def reverse_fix_salas_muebles_url(apps, schema_editor):
    Tutorial = apps.get_model('presentation', 'Tutorial')
    Tutorial.objects.filter(slug='salas-muebles').update(
        url_name='laboratory:rooms_list'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('presentation', '0009_load_more_tutorials'),
    ]

    operations = [
        migrations.RunPython(
            fix_salas_muebles_url,
            reverse_fix_salas_muebles_url,
        ),
    ]