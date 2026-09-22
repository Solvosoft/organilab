from django.db import migrations

from presentation.alerts import seed_alert_triggers


def load_triggers(apps, schema_editor):
    seed_alert_triggers(apps.get_model("laboratory", "Catalog"))


class Migration(migrations.Migration):

    dependencies = [
        ("presentation", "0013_alerts"),
    ]

    operations = [
        migrations.RunPython(load_triggers, reverse_code=migrations.RunPython.noop),
    ]
