"""Piezas comunes para armar los datasets de los reportes sin N+1.

Los reportes recorren miles de filas: todo lo que se lea por fila tiene que
venir precargado (``ShelfObject.objects.for_report()``) o resolverse contra un
mapa construido una sola vez por reporte.
"""

from collections import defaultdict

from laboratory.models import ShelfObject
from sga.models import HCodeCategory

HAZARD_CATEGORIES = ("physical", "health", "environment")


def hcode_category_map():
    """``código H`` -> categorías de peligro (física, salud, ambiente).

    Una consulta por reporte; antes eran tres por fila.
    """
    through = HCodeCategory.h_code.through
    mapping = defaultdict(set)
    rows = through.objects.values_list(
        "dangerindication_id", "hcodecategory__danger_category"
    )
    for code, category in rows:
        mapping[code].add(category)
    return mapping


def hcode_threshold_map():
    """``código H`` -> ``[(categoría, umbral en toneladas), ...]``."""
    through = HCodeCategory.h_code.through
    mapping = defaultdict(list)
    rows = through.objects.values_list(
        "dangerindication_id",
        "hcodecategory__danger_category",
        "hcodecategory__threshold",
    )
    for code, category, threshold in rows:
        mapping[code].append((category, threshold))
    return mapping


def hazards_by_category(sga_char, category_map):
    """Descripciones de los códigos H de la ficha, agrupadas por categoría.

    Lee ``h_code`` de la precarga y ordena por código para que el resultado
    no dependa del orden en que la base devuelva las filas.
    """
    result = {category: [] for category in HAZARD_CATEGORIES}
    if sga_char is None:
        return {category: "" for category in HAZARD_CATEGORIES}
    for h_code in sorted(sga_char.h_code.all(), key=lambda item: item.code):
        for category in category_map.get(h_code.code, ()):
            if category in result:
                result[category].append(h_code.description)
    return {category: " ".join(items) for category, items in result.items()}


def shelfobjects_by_furniture(furniture_list, filters=None, order_by=("pk",)):
    """``(mueble, shelfobject)`` en el orden de ``furniture_list``.

    Una consulta para todos los muebles en vez de una por mueble, y cada fila
    con su objeto, unidad, estante y ficha SGA precargados. Un filtro que cruce
    una relación a muchos puede repetir filas: se descartan las repetidas.
    """
    furniture_list = list(furniture_list)
    if not furniture_list:
        return
    queryset = (
        ShelfObject.objects.for_report()
        .filter(shelf__furniture__in=furniture_list, **(filters or {}))
        .order_by(*order_by)
    )
    grouped = defaultdict(list)
    seen = set()
    for shelfobject in queryset:
        if shelfobject.pk in seen:
            continue
        seen.add(shelfobject.pk)
        grouped[shelfobject.shelf.furniture_id].append(shelfobject)
    for furniture in furniture_list:
        for shelfobject in grouped.get(furniture.pk, ()):
            yield furniture, shelfobject


def reactive_columns(reactive, category_map):
    """Columnas comunes a los reportes de reactivos (por mueble y general)."""
    sga_char = reactive.object.get_sga_characteristic()
    hazards = hazards_by_category(sga_char, category_map)
    laboratory = reactive.in_where_laboratory
    return {
        "shelfobject_code": reactive.shelfobject_code or "",
        "name": reactive.object.name,
        "cas_id": reactive.object.cas_code if sga_char else "",
        "location": getattr(laboratory, "location", "") if laboratory else "",
        "physical_status": (
            reactive.get_physical_status_display() if reactive.physical_status else ""
        ),
        "physical": hazards["physical"],
        "health": hazards["health"],
        "environment": hazards["environment"],
        "concentration": reactive.concentration,
        "quantity": round(reactive.total_quantity, 3),
        "measurement_unit": reactive.get_measurement_unit_display(),
    }
