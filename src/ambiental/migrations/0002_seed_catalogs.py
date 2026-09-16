from django.db import migrations

from ambiental.ambiental_defaults import seed_ambiental


def load_catalogs(apps, schema_editor):
    seed_ambiental(apps.get_model("laboratory", "Catalog"))


class Migration(migrations.Migration):

    dependencies = [
        ("ambiental", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(load_catalogs, reverse_code=migrations.RunPython.noop),
    ]
