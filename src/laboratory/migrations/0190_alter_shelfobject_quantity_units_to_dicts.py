import random
import string

from django.db import migrations, models

_BOX_CODE_CHARS = string.digits + string.ascii_lowercase


def _generate_box_code(shelfobject_pk, existing_codes):
    existing = set(existing_codes)
    prefix = f"b{shelfobject_pk}-"
    while True:
        suffix = "".join(random.choices(_BOX_CODE_CHARS, k=4))
        code = f"{prefix}{suffix}"
        if code not in existing:
            return code


def convert_quantity_units_to_dicts(apps, schema_editor):
    ShelfObject = apps.get_model("laboratory", "ShelfObject")
    for obj in ShelfObject.objects.filter(is_box=True):
        old = obj.quantity_units or []
        if old and not isinstance(old[0], dict):
            new_units = []
            for units in old:
                existing_codes = [b["code"] for b in new_units]
                code = _generate_box_code(obj.pk, existing_codes)
                new_units.append({"code": code, "units": int(units)})
            obj.quantity_units = new_units
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