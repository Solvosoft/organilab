from django.db import migrations


def recalculate(apps, schema_editor):
    """Vuelve a expresar ``ShelfObject.quantity_base_unit`` en la unidad base.

    La señal ``pre_save`` sólo convertía cuando el campo venía en ``None``, pero
    su default es 0: casi todas las existencias quedaron con la cantidad cruda
    (500 en vez de 0.5 para 500 mL). Aquí se aplica la misma regla que la señal
    corregida: ``quantity / si_value``, la cantidad tal cual si la unidad ya es la
    base, y también tal cual si la unidad no tiene ``BaseUnitValues``.
    Idempotente.
    """
    ShelfObject = apps.get_model("laboratory", "ShelfObject")
    BaseUnitValues = apps.get_model("laboratory", "BaseUnitValues")

    units = {}
    for unit_id, si_value, description, base_description in BaseUnitValues.objects.values_list(
        "measurement_unit_id",
        "si_value",
        "measurement_unit__description",
        "measurement_unit_base__description",
    ):
        # Si hubiera filas repetidas para una unidad, manda la primera, igual
        # que ``get_unit_info`` fuera de un bloque ``cached_units``.
        units.setdefault(unit_id, (si_value, description, base_description))

    batch = []
    rows = ShelfObject.objects.values_list(
        "pk", "measurement_unit_id", "quantity", "quantity_base_unit"
    ).order_by("pk")
    for pk, unit_id, quantity, current in rows.iterator():
        info = units.get(unit_id)
        if info is None or quantity is None:
            value = quantity
        elif info[1] == info[2]:
            value = quantity
        else:
            value = quantity / info[0]
        if value is not None and value != current:
            batch.append(ShelfObject(pk=pk, quantity_base_unit=value))
        if len(batch) >= 1000:
            ShelfObject.objects.bulk_update(batch, ["quantity_base_unit"])
            batch = []
    if batch:
        ShelfObject.objects.bulk_update(batch, ["quantity_base_unit"])


class Migration(migrations.Migration):

    dependencies = [
        ("laboratory", "0223_normalize_dataconfig"),
    ]

    operations = [
        migrations.RunPython(recalculate, migrations.RunPython.noop, elidable=True),
    ]
