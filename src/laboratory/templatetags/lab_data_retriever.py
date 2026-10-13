from django import template
from django.db.models import Count, Q

from laboratory.models import Object

register = template.Library()

SHELFOBJECT_PATH = "laboratoryroom__furniture__shelf__shelfobject"


def annotate_object_counts(queryset):
    """Cuenta materiales, equipos y reactivos de cada laboratorio en la consulta.

    La tarjeta de laboratorio pintaba tres ``COUNT`` por laboratorio; con esto
    los filtros de abajo leen el valor ya calculado.
    """
    counts = {
        "materials_count": Object.MATERIAL,
        "equipment_count": Object.EQUIPMENT,
        "reactives_count": Object.REACTIVE,
    }
    return queryset.annotate(
        **{
            name: Count(
                SHELFOBJECT_PATH,
                filter=Q(**{SHELFOBJECT_PATH + "__object__type": object_type}),
            )
            for name, object_type in counts.items()
        }
    )


def _count(lab, attribute, object_type):
    value = getattr(lab, attribute, None)
    if value is not None:
        return value
    return Object.objects.filter(
        type=object_type, shelfobject__shelf__furniture__labroom__laboratory=lab
    ).count()


@register.filter()
def get_materiales_lab(lab):
    return _count(lab, "materials_count", Object.MATERIAL)


@register.filter()
def get_equipo_lab(lab):
    return _count(lab, "equipment_count", Object.EQUIPMENT)


@register.filter()
def get_reactivos_lab(lab):
    return _count(lab, "reactives_count", Object.REACTIVE)
