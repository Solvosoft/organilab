from django import template
from laboratory.models import Object

register = template.Library()

@register.filter()
def get_materiales_lab(lab):
    return Object.objects.filter(type=Object.MATERIAL, shelfobject__shelf__furniture__labroom__laboratory=lab).count()


@register.filter()
def get_equipo_lab(lab):
    return Object.objects.filter(type=Object.EQUIPMENT, shelfobject__shelf__furniture__labroom__laboratory=lab).count()


@register.filter()
def get_reactivos_lab(lab):
    return  Object.objects.filter(type=Object.REACTIVE, shelfobject__shelf__furniture__labroom__laboratory=lab).count()
