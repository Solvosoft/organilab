import datetime
from pathlib import Path

from django.utils.text import slugify


def upload_files(instance, filename):
    date = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    path = Path(filename)
    extension = path.suffix.lower()
    name = slugify(path.stem)
    model_name = str(type(instance).__name__).lower()
    return f"{model_name}/{date}/{name}{extension}"


def get_shelfobject_conversion_from_two_units(shelfobject_unit, shelf_unit, amount):
    query = BaseUnitValues.objects.filter(measurement_unit=shelfobject_unit)
    query2 = BaseUnitValues.objects.filter(measurement_unit=shelf_unit)
    if shelf_unit is None:
        return amount
    if query.exists() and query2.exists():
        unit1 = query.first()
        value1 = unit1.si_value

        unit2 = query2.first()
        value2 = unit2.si_value

        if unit1.measurement_unit.description == "Unidades":
            return amount

        if value1 > value2:
            result = amount / (value1 / value2)
        else:
            result = amount * (value2 / value1)
        return result
    else:
        return None
