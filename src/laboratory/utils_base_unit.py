from laboratory.models import BaseUnitValues

# from laboratory.utils_base_unit import get_conversion_units


def get_base_unit(unit):
    unitbase = None
    query = BaseUnitValues.objects.filter(measurement_unit=unit)
    if query.exists() and query.first().measurement_unit_base:
        unitbase = query.first().measurement_unit_base

    return unitbase

def get_conversion_units(unit, amount):
    query = BaseUnitValues.objects.filter(measurement_unit=unit)
    if query.exists():
        unit = query.first()
        base = unit.measurement_unit
        value = unit.si_value

        if base.description in ["Mililitros", "Milímetros", "Gramos", "Centimetros", "Miligramos", "Atmósfera"]:


            result = amount / value

            return result

        if base.description in ["Litros", "Kilogramos", "Metros", "Pascales",
                                "Unidades", "PSI", "Metro cúbico"]:

            return amount


    else:
        return None
