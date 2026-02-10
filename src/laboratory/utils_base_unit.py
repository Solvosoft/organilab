from laboratory.models import BaseUnitValues
from laboratory.models import Shelf

# from laboratory.utils_base_unit import get_conversion_units
# from laboratory.utils_base_unit import get_conversion_from_two_units


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

        if base.description == unit.measurement_unit_base.description:
            return amount

        result = amount / value
        return result

    else:
        return None


def get_conversion_from_two_units(shelfobject_unit, shelf_unit, amount):
    query = BaseUnitValues.objects.filter(measurement_unit=shelfobject_unit)
    query2 = BaseUnitValues.objects.filter(measurement_unit=shelf_unit)
    if shelf_unit==None:
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


def get_related_units(unit, queryset):
    base_unit = BaseUnitValues.objects.filter(measurement_unit=unit)

    if base_unit.exists():
        base_unit = base_unit.first()

        subunits = BaseUnitValues.objects.filter(
            measurement_unit_base=base_unit.measurement_unit_base
        )

        subunit_ids = subunits.values_list("measurement_unit__pk", flat=True)

        return queryset.filter(pk__in=subunit_ids)


def get_related_units_from_laboratory(unit):
    subunit_ids = []
    base_unit = BaseUnitValues.objects.filter(measurement_unit=unit)

    if base_unit.exists():
        base_unit = base_unit.first()

        subunits = BaseUnitValues.objects.filter(
            measurement_unit_base=base_unit.measurement_unit_base
        )

        subunit_ids = subunits.values_list("measurement_unit__pk", flat=True)

    return subunit_ids
