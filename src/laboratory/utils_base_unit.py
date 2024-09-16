from laboratory.models import BaseUnitValues

# from laboratory.utils_base_unit import get_conversion_units


def get_base_unit(unit): #This function is used within the save_object_report_precursor function in task_utils.py
    query = BaseUnitValues.objects.filter(measurement_unit=unit)
    if query.exists():
        unit = query.first().measurement_unit_base
        return unit
    else:
        return None

def get_conversion_units(unit, amount):
    query = BaseUnitValues.objects.filter(measurement_unit=unit)
    if query.exists():
        unit = query.first()
        base = unit.measurement_unit_base
        value = unit.si_value

        if base.description in ["Mililitros", "Milímetros", "Gramos", "Centimetros", "Miligramos"]:

            converted_amount = amount * value
            result = converted_amount/value

            return result

        if base.description in ["Litros", "Kilogramos", "Metros", "Pascales",
                                "Unidades", "PSI", "Atmósfera", "Metro cúbico"]:

            converted_amount = amount * value
            return converted_amount


    else:
        return None








