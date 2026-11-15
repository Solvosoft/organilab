from django.db import migrations

# Copia congelada: el disparador pasó a ser un código de djgentelella.alerts
# (0015) y presentation.alerts ya no siembra el catálogo.
TRIGGERS = ("Variación porcentual", "Umbral absoluto", "Sin registro")


def load_triggers(apps, schema_editor):
    Catalog = apps.get_model("laboratory", "Catalog")
    for description in TRIGGERS:
        Catalog.objects.get_or_create(key="alert_trigger", description=description)


class Migration(migrations.Migration):

    dependencies = [
        ("presentation", "0013_alerts"),
    ]

    operations = [
        migrations.RunPython(load_triggers, reverse_code=migrations.RunPython.noop),
    ]
