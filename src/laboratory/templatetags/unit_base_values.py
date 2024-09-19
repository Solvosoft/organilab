from django import template

from laboratory.utils_base_unit import get_base_unit, get_conversion_units

register = template.Library()

@register.simple_tag()
def get_unit_base(unit):
    unitbase = get_base_unit(unit)

    if unitbase:
        return unitbase.description

    return "--"

@register.simple_tag(takes_context=False)
def get_conversion_result(unit, amount):
    result = get_conversion_units(unit, amount)

    if result:
        return result

    return 0
