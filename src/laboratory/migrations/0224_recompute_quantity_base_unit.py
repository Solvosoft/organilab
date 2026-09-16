from django.db import migrations


def recompute(apps, schema_editor):
    """Recalcula ``ShelfObject.quantity_base_unit`` con la conversión real.

    La señal copiaba la cantidad sin convertir, así que las sumas por unidad
    base (gráficos de riesgo, reportes de precursores) mezclaban unidades.
    Replica ``laboratory.utils_base_unit.get_conversion_units``. Idempotente.
    """
    ShelfObject = apps.get_model("laboratory", "ShelfObject")
    BaseUnitValues = apps.get_model("laboratory", "BaseUnitValues")

    factors = {}
    for unit in BaseUnitValues.objects.select_related("measurement_unit", "measurement_unit_base"):
        base = unit.measurement_unit_base
        same = base is not None and unit.measurement_unit.description == base.description
        factors[unit.measurement_unit_id] = None if same else unit.si_value

    batch = []
    queryset = ShelfObject.objects.only("pk", "quantity", "measurement_unit_id", "quantity_base_unit")
    for shelfobject in queryset.iterator(chunk_size=2000):
        quantity = shelfobject.quantity
        factor = factors.get(shelfobject.measurement_unit_id)
        value = quantity / factor if factor else quantity
        if value != shelfobject.quantity_base_unit:
            shelfobject.quantity_base_unit = value
            batch.append(shelfobject)
        if len(batch) >= 2000:
            ShelfObject.objects.bulk_update(batch, ["quantity_base_unit"])
            batch = []
    if batch:
        ShelfObject.objects.bulk_update(batch, ["quantity_base_unit"])


class Migration(migrations.Migration):

    dependencies = [
        ("laboratory", "0223_normalize_dataconfig"),
    ]

    operations = [
        migrations.RunPython(recompute, migrations.RunPython.noop, elidable=True),
    ]
