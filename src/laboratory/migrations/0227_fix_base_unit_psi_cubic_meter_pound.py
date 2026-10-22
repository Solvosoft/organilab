from django.db import migrations

FIXES = (
    ("PSI", "Pascales", 0.0001450377),
    ("Metro cúbico", "Litros", 0.001),
    ("Libra", "Kilogramos", 2.20462),
)
PREVIOUS = {"PSI": 0.0001450377, "Metro cúbico": 0.001, "Libra": 1}


def _unit(Catalog, description):
    return Catalog.objects.filter(key="units", description=description).first()


def _recalculate(ShelfObject, unit, si_value, same_as_base):
    for pk, quantity in ShelfObject.objects.filter(measurement_unit=unit).values_list("pk", "quantity"):
        if quantity is not None:
            value = quantity if same_as_base else quantity / si_value
            ShelfObject.objects.filter(pk=pk).update(quantity_base_unit=value)


def fix_base_units(apps, schema_editor):
    Catalog = apps.get_model("laboratory", "Catalog")
    BaseUnitValues = apps.get_model("laboratory", "BaseUnitValues")
    ShelfObject = apps.get_model("laboratory", "ShelfObject")
    for description, base_description, si_value in FIXES:
        unit = _unit(Catalog, description)
        base = _unit(Catalog, base_description)
        if unit is None or base is None:
            continue
        updated = BaseUnitValues.objects.filter(measurement_unit=unit).update(
            measurement_unit_base=base, si_value=si_value
        )
        if updated:
            _recalculate(ShelfObject, unit, si_value, same_as_base=False)


def restore_base_units(apps, schema_editor):
    Catalog = apps.get_model("laboratory", "Catalog")
    BaseUnitValues = apps.get_model("laboratory", "BaseUnitValues")
    ShelfObject = apps.get_model("laboratory", "ShelfObject")
    for description, si_value in PREVIOUS.items():
        unit = _unit(Catalog, description)
        if unit is None:
            continue
        updated = BaseUnitValues.objects.filter(measurement_unit=unit).update(
            measurement_unit_base=unit, si_value=si_value
        )
        if updated:
            _recalculate(ShelfObject, unit, si_value, same_as_base=True)


class Migration(migrations.Migration):

    dependencies = [
        ("laboratory", "0226_delete_root_copies_objectlogchange"),
    ]

    operations = [
        migrations.RunPython(fix_base_units, reverse_code=restore_base_units),
    ]
