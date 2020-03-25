from django import template
from django.db.models import Q

from laboratory.models import Object

register = template.Library()


@register.filter()
def get_materiales_lab(lab):
    materiales = Object.objects.filter(Q(type='1') & Q(laboratory__in=[lab])).count()
    return materiales


@register.filter()
def get_equipo_lab(lab):
    equipo = Object.objects.filter(Q(type='2') & Q(laboratory__in=[lab])).count()
    return equipo


@register.filter()
def get_reactivos_lab(lab):
    reactivos = Object.objects.filter(Q(type='0') & Q(laboratory__in=[lab])).count()
    return reactivos
