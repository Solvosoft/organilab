import contextvars
from contextlib import contextmanager

from laboratory.models import BaseUnitValues, Catalog
from laboratory.models import Shelf

# from laboratory.utils_base_unit import get_conversion_units
# from laboratory.utils_base_unit import get_conversion_from_two_units


class UnitInfo:
    """Lo que hace falta de un ``BaseUnitValues`` para convertir cantidades."""

    __slots__ = ("si_value", "base_id", "base_description", "description")

    def __init__(self, si_value, base_id, base_description, description):
        self.si_value = si_value
        self.base_id = base_id
        self.base_description = base_description
        self.description = description


_unit_map = contextvars.ContextVar("organilab_unit_map", default=None)


def load_unit_map():
    """``measurement_unit_id`` -> :class:`UnitInfo`, en una sola consulta.

    El catálogo de unidades es pequeño: cargarlo entero cuesta menos que una
    sola de las consultas que hacía cada conversión.
    """
    rows = BaseUnitValues.objects.values_list(
        "measurement_unit_id",
        "si_value",
        "measurement_unit_base_id",
        "measurement_unit_base__description",
        "measurement_unit__description",
    )
    return {row[0]: UnitInfo(*row[1:]) for row in rows}


@contextmanager
def cached_units():
    """Las conversiones dentro del bloque comparten un mapa de unidades.

    Pensado para reportes y gráficos que convierten miles de cantidades: el
    mapa se carga una vez al entrar y se descarta al salir, así nunca queda
    desfasado frente a ediciones del catálogo.  Fuera del bloque cada
    conversión consulta su unidad, como antes.
    """
    if _unit_map.get() is not None:
        yield _unit_map.get()
        return
    token = _unit_map.set(load_unit_map())
    try:
        yield _unit_map.get()
    finally:
        _unit_map.reset(token)


def _unit_pk(unit):
    return getattr(unit, "pk", unit)


def get_unit_info(unit):
    """:class:`UnitInfo` de ``unit`` (instancia o pk), o ``None``."""
    if unit is None:
        return None
    unit_pk = _unit_pk(unit)
    mapping = _unit_map.get()
    if mapping is not None:
        return mapping.get(unit_pk)
    row = (
        BaseUnitValues.objects.filter(measurement_unit_id=unit_pk)
        .values_list(
            "si_value",
            "measurement_unit_base_id",
            "measurement_unit_base__description",
            "measurement_unit__description",
        )
        .first()
    )
    return UnitInfo(*row) if row else None


def get_base_unit(unit):
    info = get_unit_info(unit)
    if info is None or info.base_id is None:
        return None
    return Catalog.objects.filter(pk=info.base_id).first()


def get_conversion_units(unit, amount):
    info = get_unit_info(unit)
    if info is None:
        return None
    if info.description == info.base_description:
        return amount
    return amount / info.si_value


def get_conversion_from_base_unit(unit, amount):
    """Inverso de :func:`get_conversion_units`: de la unidad base a ``unit``."""
    info = get_unit_info(unit)
    if info is None:
        return None
    if info.description == info.base_description:
        return amount
    return amount * info.si_value


def get_unit_family(unit):
    """``measurement_unit_id`` de las unidades con la misma unidad base que ``unit``.

    ``None`` si la unidad no tiene base conocida: no es comparable con ninguna otra.
    """
    info = get_unit_info(unit)
    if info is None or info.base_id is None:
        return None
    return list(
        BaseUnitValues.objects.filter(measurement_unit_base_id=info.base_id).values_list(
            "measurement_unit_id", flat=True
        )
    )


def get_conversion_from_two_units(shelfobject_unit, shelf_unit, amount):
    if shelf_unit is None:
        return amount
    unit1 = get_unit_info(shelfobject_unit)
    unit2 = get_unit_info(shelf_unit)
    if unit1 is None or unit2 is None:
        return None
    if unit1.description == "Unidades":
        return amount
    value1, value2 = unit1.si_value, unit2.si_value
    if value1 > value2:
        return amount / (value1 / value2)
    return amount * (value2 / value1)


def get_related_units(unit, queryset):
    """Unidades convertibles con ``unit``, o ``None`` si no tiene unidad base.

    ``None`` significa que la unidad no es convertible, no que no haya
    resultados: quien llame debe rechazar la conversión en vez de tratarlo
    como una lista vacía.
    """
    base_unit = BaseUnitValues.objects.filter(measurement_unit=unit)

    if base_unit.exists():
        base_unit = base_unit.first()

        subunits = BaseUnitValues.objects.filter(
            measurement_unit_base=base_unit.measurement_unit_base
        )

        subunit_ids = subunits.values_list("measurement_unit__pk", flat=True)

        return queryset.filter(pk__in=subunit_ids)

    return None


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
