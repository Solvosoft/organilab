from django.db import migrations, models


def convert_quantity_units_to_dicts(apps, schema_editor):
    ShelfObject = apps.get_model("laboratory", "ShelfObject")
    for obj in ShelfObject.objects.filter(is_box=True):
        old = obj.quantity_units or []
        if old and not isinstance(old[0], dict):
            obj.quantity_units = [
                {"code": f"b-{obj.pk}-{i + 1:04d}", "units": int(units)}
                for i, units in enumerate(old)
            ]
            obj.save(update_fields=["quantity_units"])


def revert_quantity_units_to_ints(apps, schema_editor):
    ShelfObject = apps.get_model("laboratory", "ShelfObject")
    for obj in ShelfObject.objects.filter(is_box=True):
        old = obj.quantity_units or []
        if old and isinstance(old[0], dict):
            obj.quantity_units = [entry["units"] for entry in old]
            obj.save(update_fields=["quantity_units"])


class Migration(migrations.Migration):

    dependencies = [
        ("laboratory", "0189_shelfobject_units_per_box_remove_quantity_box"),
    ]

    operations = [
        migrations.AlterField(
            model_name="shelfobject",
            name="quantity_units",
            field=models.JSONField(
                default=list,
                help_text='List of box entries, each with "code" (e.g. "b-0001") and "units" (integer count)',
                verbose_name="Units per box",
            ),
        ),
        migrations.RunPython(
            convert_quantity_units_to_dicts,
            reverse_code=revert_quantity_units_to_ints,
        ),
    ]