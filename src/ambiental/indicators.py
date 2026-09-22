"""Indicadores ambientales: consumo dividido por su base, y comparación de períodos.

Funciones puras sobre la base de datos, sin petición: las usan los reportes, los
gráficos y las alertas. Un registro cuenta en el período de su ``period_end``.

Unidades: si un mismo recurso tiene registros en unidades distintas en el período,
no se suman (no hay conversión en v1). El resultado lo marca con ``mixed_units`` y el
valor queda en ``None``: un número calculado sumando litros y metros cúbicos sería
peor que ningún número.
"""
from decimal import Decimal

from ambiental.models import ConsumptionRecord
from ambiental.normalization import get_base

INDICATOR_PRECISION = Decimal("0.0001")
PERCENT_PRECISION = Decimal("0.01")


def records_for(organization, resource_type, date_from, date_to, building=None, buildings=None):
    """Registros del recurso en el rango; ``buildings`` acota a los edificios visibles."""
    queryset = ConsumptionRecord.objects.filter(
        organization=organization,
        point__resource_type=resource_type,
        period_end__range=(date_from, date_to),
    )
    if building is not None:
        queryset = queryset.filter(point__building=building)
    if buildings is not None:
        queryset = queryset.filter(point__building__in=buildings)
    return queryset


def totals_by_unit(queryset):
    totals = {}
    for unit, quantity in queryset.values_list("unit__description", "quantity"):
        totals[unit] = totals.get(unit, Decimal(0)) + quantity
    return totals


def single_total(queryset):
    """``(total, unidad, mixed_units)`` de un conjunto de registros."""
    totals = totals_by_unit(queryset)
    if len(totals) == 1:
        unit, total = next(iter(totals.items()))
        return total, unit, False
    return None, None, len(totals) > 1


def total_cost(queryset):
    costs = [cost for cost in queryset.values_list("total_cost", flat=True) if cost is not None]
    return sum(costs, Decimal(0)) if costs else None


def compute_indicator(organization, building, resource_type, normalizer, date_from, date_to):
    """El consumo del edificio en el período dividido por su base del año de ``date_to``.

    Devuelve un diccionario auditable: además del valor trae el total crudo, la unidad
    y la base usada (con su año, que dice si fue heredada).
    """
    records = records_for(organization, resource_type, date_from, date_to, building)
    total, unit, mixed = single_total(records)
    base = get_base(organization, building, normalizer, date_to.year)
    value = None
    if total is not None and base is not None and base.value:
        value = (total / base.value).quantize(INDICATOR_PRECISION)
    return {
        "value": value,
        "raw_total": total,
        "unit": unit,
        "mixed_units": mixed,
        "base": base.value if base else None,
        "base_year": base.year if base else None,
        "records": records.count(),
    }


def variation(previous, current):
    """Variación absoluta y porcentual; sin referencia (o referencia 0) no hay %."""
    if previous is None or current is None:
        return {"absolute": None, "percent": None}
    absolute = current - previous
    percent = None
    if previous:
        percent = (absolute / previous * 100).quantize(PERCENT_PRECISION)
    return {"absolute": absolute, "percent": percent}


def compare_periods(organization, resource_type, periods, building=None, buildings=None):
    """Totales de cada período y su variación respecto al período anterior de la lista."""
    rows = []
    previous = None
    for date_from, date_to in periods:
        records = records_for(organization, resource_type, date_from, date_to, building, buildings)
        total, unit, mixed = single_total(records)
        row = {
            "date_from": date_from,
            "date_to": date_to,
            "quantity": total,
            "unit": unit,
            "mixed_units": mixed,
            "cost": total_cost(records),
        }
        row.update(variation(previous["quantity"] if previous else None, total))
        if previous and previous["unit"] and unit and previous["unit"] != unit:
            row.update({"absolute": None, "percent": None, "mixed_units": True})
        rows.append(row)
        previous = row
    return rows
