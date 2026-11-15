"""El disparador de la regla deja de ser un Catalog y pasa a ser un código de
``djgentelella.alerts`` (absolute, percent, missing, due)."""
from django.db import migrations, models

DESCRIPTION_TO_CODE = {
    "Variación porcentual": "percent",
    "Umbral absoluto": "absolute",
    "Sin registro": "missing",
}


def to_codes(apps, schema_editor):
    AlertRule = apps.get_model("presentation", "AlertRule")
    for rule in AlertRule.objects.select_related("trigger_catalog"):
        description = rule.trigger_catalog.description if rule.trigger_catalog_id else ""
        rule.trigger = DESCRIPTION_TO_CODE.get(description, description[:100])
        threshold = dict(rule.threshold or {})
        if "months" in threshold:
            threshold["periods"] = threshold.pop("months")
        rule.threshold = threshold
        rule.save(update_fields=["trigger", "threshold"])


def to_catalog(apps, schema_editor):
    AlertRule = apps.get_model("presentation", "AlertRule")
    Catalog = apps.get_model("laboratory", "Catalog")
    code_to_description = {code: description for description, code in DESCRIPTION_TO_CODE.items()}
    for rule in AlertRule.objects.all():
        description = code_to_description.get(rule.trigger)
        if description is None:
            continue
        rule.trigger_catalog, _created = Catalog.objects.get_or_create(
            key="alert_trigger", description=description
        )
        threshold = dict(rule.threshold or {})
        if "periods" in threshold:
            threshold["months"] = threshold.pop("periods")
        rule.threshold = threshold
        rule.save(update_fields=["trigger_catalog", "threshold"])


class Migration(migrations.Migration):

    dependencies = [
        ("presentation", "0014_seed_alert_triggers"),
        ("laboratory", "0229_equipment_iso17025_data"),
    ]

    operations = [
        migrations.RenameField("alertrule", "trigger", "trigger_catalog"),
        migrations.AlterField(
            model_name="alertrule",
            name="trigger_catalog",
            field=models.ForeignKey(
                null=True, on_delete=models.deletion.PROTECT, related_name="+", to="laboratory.catalog",
            ),
        ),
        migrations.AddField(
            model_name="alertrule",
            name="trigger",
            field=models.CharField(default="", max_length=100, verbose_name="Trigger"),
            preserve_default=False,
        ),
        migrations.RunPython(to_codes, reverse_code=to_catalog),
        migrations.RemoveField("alertrule", "trigger_catalog"),
    ]
