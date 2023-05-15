from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django import template
from django.utils.safestring import mark_safe

from laboratory.shelf_utils import get_dataconfig

register = template.Library()

@register.filter
def display_furniture(furniture):
    dataconfig=get_dataconfig(furniture.dataconfig)
    dev = render_to_string('laboratory/shelf_card.html', context={'data': dataconfig})

    return mark_safe(dev)