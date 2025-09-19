from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django import template
from django.utils.safestring import mark_safe

from laboratory.shelf_utils import get_dataconfig

register = template.Library()


@register.simple_tag(takes_context=True)
def display_furniture(context, furniture):
    dataconfig = get_dataconfig(furniture.dataconfig)
    context_render = {
        "request": context["request"],
        "laboratory": context["laboratory"],
        "org_pk": context["org_pk"],
        "data": dataconfig,
        "laboratoryroom": furniture.labroom,
        "furniture": furniture,
    }
    dev = render_to_string("laboratory/shelf_card.html", context=context_render)
    return mark_safe(dev)
