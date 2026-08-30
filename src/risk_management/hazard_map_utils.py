import logging

from laboratory.models import (
    BaseUnitValues,
    Furniture,
    LaboratoryRoom,
    Object,
    Shelf,
    ShelfObject,
)
from laboratory import dataconfig
from laboratory.utils_base_unit import get_conversion_units
from risk_management.compatibility_utils import (
    COMPAT_LABELS,
    H_CODE_TO_CLASS,
    ODS_STYLES,
    COMPAT_TO_STYLE,
    get_compatibility_reason,
    get_h_code_compatibility,
)

logger = logging.getLogger("organilab.report")

HAZARD_COLORS = {
    'V': ODS_STYLES['green_bg'],   # #00B050
    'A': ODS_STYLES['yellow_bg'],  # #FFD700
    'R': ODS_STYLES['red_bg'],     # #FF0000
    '-': ODS_STYLES['gray_bg'],    # #D9D9D9
}


def collect_room_shelf_hcodes(room):
    """Collect h_codes per shelf for all shelves in a LaboratoryRoom.

    Returns: {shelf_pk: {"name": str, "h_codes": set(str), "substances": [str]}}
    """
    shelf_data = {}
    shelf_objects = ShelfObject.objects.filter(
        shelf__furniture__labroom=room,
        object__type=Object.REACTIVE,
    ).select_related(
        'object', 'shelf', 'shelf__furniture'
    ).prefetch_related(
        'object__substancharacteristics_object__h_code'
    )

    for so in shelf_objects:
        shelf = so.shelf
        obj = so.object
        if shelf.pk not in shelf_data:
            shelf_data[shelf.pk] = {
                "name": shelf.name,
                "h_codes": set(),
                "substances": [],
                "furniture_pk": shelf.furniture_id,
                "labroom_pk": shelf.furniture.labroom_id,
            }

        sga_char = obj.substancharacteristics_object.first()
        if sga_char:
            h_codes = list(sga_char.h_code.values_list('code', flat=True))
            if h_codes:
                shelf_data[shelf.pk]["h_codes"].update(h_codes)
                codes_str = ", ".join(sorted(h_codes))
                shelf_data[shelf.pk]["substances"].append(
                    "%s (%s)" % (obj.name, codes_str)
                )
            else:
                shelf_data[shelf.pk]["substances"].append(obj.name)
        else:
            shelf_data[shelf.pk]["substances"].append(obj.name)

    return shelf_data


def compute_shelf_danger(shelf_pk, shelf_hcodes, all_shelves_data):
    """Compute worst-case compatibility for a shelf vs all others in room.

    Returns: (compat_code, worst_pair_description)
        compat_code: 'R', 'A', 'V', or '-'
        worst_pair_description: human-readable string for worst pair
    """
    if not shelf_hcodes:
        return '-', ''

    worst = 'V'
    worst_pair = ''

    for other_pk, other_data in all_shelves_data.items():
        if other_pk == shelf_pk:
            continue
        other_hcodes = other_data["h_codes"]
        if not other_hcodes:
            continue

        for code_a in shelf_hcodes:
            for code_b in other_hcodes:
                compat = get_h_code_compatibility(code_a, code_b)
                if compat == 'R' and worst != 'R':
                    worst = 'R'
                    class_a = H_CODE_TO_CLASS.get(code_a, '')
                    class_b = H_CODE_TO_CLASS.get(code_b, '')
                    reason = ''
                    if class_a and class_b:
                        reason = get_compatibility_reason(class_a, class_b)
                    worst_pair = "%s vs %s: %s" % (code_a, code_b, reason)
                elif compat == 'A' and worst == 'V':
                    worst = 'A'
                    worst_pair = "%s vs %s: %s" % (
                        code_a, code_b, COMPAT_LABELS.get('A', '')
                    )

        if worst == 'R':
            break

    return worst, worst_pair


COMPAT_SUMMARY_KEYS = {"V": "green", "A": "yellow", "R": "red", "-": "gray"}


def _empty_summary():
    return {"green": 0, "yellow": 0, "red": 0, "gray": 0}


def _kg_conversion_map():
    """``measurement_unit_id`` -> ``True`` cuando la unidad se mide en kilogramos.

    Una sola consulta.  Antes se preguntaba por ``BaseUnitValues`` una vez por
    objeto, dentro del bucle.
    """
    units = BaseUnitValues.objects.select_related(
        "measurement_unit_base"
    ).filter(measurement_unit_base__description="Kilogramos")
    return set(units.values_list("measurement_unit_id", flat=True))


def compute_tonnage_aggregates(laboratory):
    """Masa de reactivos en kg y toneladas, por laboratorio, sala y mueble.

    El total del laboratorio es lo que consumía el mapa de peligros; los
    desgloses por sala y por mueble son lo que faltaba para razonar sobre
    riesgo por zona y no sólo por laboratorio entero.
    """
    kg_units = _kg_conversion_map()
    totals = {"laboratory": 0.0, "rooms": {}, "furniture": {}}

    shelf_objects = ShelfObject.objects.filter(
        in_where_laboratory=laboratory,
        object__type=Object.REACTIVE,
    ).select_related("measurement_unit", "shelf__furniture")

    for so in shelf_objects:
        if so.measurement_unit_id is None or so.quantity is None:
            continue
        if so.measurement_unit_id not in kg_units:
            continue
        converted = get_conversion_units(so.measurement_unit, float(so.quantity))
        if converted is None:
            continue
        totals["laboratory"] += converted
        furniture = so.shelf.furniture if so.shelf_id else None
        if furniture is None:
            continue
        totals["furniture"][furniture.pk] = (
            totals["furniture"].get(furniture.pk, 0.0) + converted
        )
        totals["rooms"][furniture.labroom_id] = (
            totals["rooms"].get(furniture.labroom_id, 0.0) + converted
        )

    def as_tonnage(kilograms):
        return {
            "kilograms": round(kilograms, 4),
            "tons": round(kilograms / 1000, 6),
        }

    return {
        "laboratory": as_tonnage(totals["laboratory"]),
        "rooms": {pk: as_tonnage(kg) for pk, kg in totals["rooms"].items()},
        "furniture": {pk: as_tonnage(kg) for pk, kg in totals["furniture"].items()},
    }


def compute_lab_tonnage(laboratory):
    """Total del laboratorio.  Se conserva: es lo que consume el reporte."""
    return compute_tonnage_aggregates(laboratory)["laboratory"]


def compute_lab_risk(laboratory, rooms=None):
    """El único constructor de riesgo espacial del proyecto.

    Devuelve el color y los códigos H de cada estante, las alertas de
    incompatibilidad y los recuentos por laboratorio y por sala.  Lo consumen
    **tanto el mapa de peligros como el árbol del labview**, de modo que la
    pantalla y el reporte no puedan divergir: si el mapa dice que un estante es
    rojo, el reporte dice lo mismo porque es el mismo cálculo.
    """
    if rooms is None:
        rooms = LaboratoryRoom.objects.filter(laboratory=laboratory)

    shelf_colors, shelf_hcodes, alerts = {}, {}, []
    summary = _empty_summary()
    rooms_summary = {}

    for room in rooms:
        all_shelves_data = collect_room_shelf_hcodes(room)
        room_summary = _empty_summary()

        for shelf_pk, sdata in all_shelves_data.items():
            compat_code, worst_pair = compute_shelf_danger(
                shelf_pk, sdata["h_codes"], all_shelves_data
            )
            shelf_colors[shelf_pk] = {
                "compat_code": compat_code,
                "color": HAZARD_COLORS.get(compat_code, HAZARD_COLORS["-"]),
                "worst_pair": worst_pair,
                "substances": sdata["substances"],
                "name": sdata["name"],
            }
            shelf_hcodes[shelf_pk] = sorted(sdata["h_codes"])
            key = COMPAT_SUMMARY_KEYS.get(compat_code, "gray")
            summary[key] += 1
            room_summary[key] += 1

        before = len(alerts)
        _collect_alerts(all_shelves_data, alerts)
        rooms_summary[room.pk] = {
            "summary": room_summary,
            "alerts": len(alerts) - before,
        }

    return {
        "shelf_colors": shelf_colors,
        "shelf_hcodes": shelf_hcodes,
        "alerts": alerts,
        "summary": summary,
        "rooms": rooms_summary,
    }


def build_lab_hazard_map(laboratory):
    """Datos completos del mapa de peligros de un laboratorio.

    El cálculo de riesgo ya no vive aquí: lo hace ``compute_lab_risk``, que es
    el mismo que alimenta el árbol del labview.  Este envoltorio sólo le da la
    forma que esperan las plantillas del reporte.
    """
    rooms = list(LaboratoryRoom.objects.filter(laboratory=laboratory))
    risk = compute_lab_risk(laboratory, rooms=rooms)
    shelf_colors = risk["shelf_colors"]

    rooms_data = []
    for room in rooms:
        furniture_list = [
            {
                "name": furniture.name,
                "pk": furniture.pk,
                "grid": _build_furniture_grid(furniture, shelf_colors),
            }
            for furniture in Furniture.objects.filter(labroom=room)
        ]
        rooms_data.append({"name": room.name, "furniture_list": furniture_list})

    return {
        "laboratory": laboratory.name,
        "laboratory_pk": laboratory.pk,
        "rooms": rooms_data,
        "summary": risk["summary"],
        "alerts": risk["alerts"],
        "tonnage": compute_lab_tonnage(laboratory),
    }


def _build_furniture_grid(furniture, shelf_colors):
    """Cuadrícula del mueble, resuelta en una sola consulta.

    El parseo lo hace ``laboratory.dataconfig``: antes este módulo tenía su
    propio parser y consultaba ``Shelf.objects.get(pk=...)`` dentro del doble
    bucle, un N+1 por celda.  Las filas son irregulares y se respetan tal cual.
    """
    grid = []
    matrix = dataconfig.parse(furniture.dataconfig)
    if not matrix:
        shelves = Shelf.objects.filter(furniture=furniture)
        if shelves.exists():
            row_shelves = [_shelf_to_dict(shelf, shelf_colors) for shelf in shelves]
            grid.append([{"shelves": row_shelves}])
        return grid

    for row in dataconfig.resolve_shelves(matrix):
        grid.append(
            [
                {"shelves": [_shelf_to_dict(shelf, shelf_colors) for shelf in cell]}
                for cell in row
            ]
        )
    return grid


def _shelf_to_dict(shelf, shelf_colors):
    """Convert a shelf to a dict with hazard color info."""
    if shelf.pk in shelf_colors:
        info = shelf_colors[shelf.pk]
        return {
            "pk": shelf.pk,
            "name": info["name"],
            "color": info["color"],
            "compat_code": info["compat_code"],
            "substances": info["substances"],
            "worst_pair": info["worst_pair"],
        }
    return {
        "pk": shelf.pk,
        "name": shelf.name,
        "color": HAZARD_COLORS['-'],
        "compat_code": "-",
        "substances": [],
        "worst_pair": "",
    }


def _collect_alerts(all_shelves_data, alerts):
    """Collect RED incompatibility alerts between shelf pairs in a room."""
    shelf_pks = list(all_shelves_data.keys())
    seen_pairs = set()

    for i, pk_a in enumerate(shelf_pks):
        hcodes_a = all_shelves_data[pk_a]["h_codes"]
        if not hcodes_a:
            continue
        for pk_b in shelf_pks[i + 1:]:
            hcodes_b = all_shelves_data[pk_b]["h_codes"]
            if not hcodes_b:
                continue
            pair_key = (min(pk_a, pk_b), max(pk_a, pk_b))
            if pair_key in seen_pairs:
                continue

            for code_a in hcodes_a:
                for code_b in hcodes_b:
                    compat = get_h_code_compatibility(code_a, code_b)
                    if compat == 'R':
                        class_a = H_CODE_TO_CLASS.get(code_a, '')
                        class_b = H_CODE_TO_CLASS.get(code_b, '')
                        reason = ''
                        if class_a and class_b:
                            reason = get_compatibility_reason(class_a, class_b)
                        alerts.append({
                            "shelf_a": all_shelves_data[pk_a]["name"],
                            "shelf_b": all_shelves_data[pk_b]["name"],
                            "shelf_a_pk": pk_a,
                            "shelf_b_pk": pk_b,
                            "furniture_a_pk": all_shelves_data[pk_a]["furniture_pk"],
                            "furniture_b_pk": all_shelves_data[pk_b]["furniture_pk"],
                            "labroom_a_pk": all_shelves_data[pk_a]["labroom_pk"],
                            "labroom_b_pk": all_shelves_data[pk_b]["labroom_pk"],
                            "code_a": code_a,
                            "code_b": code_b,
                            "reason": reason,
                        })
                        seen_pairs.add(pair_key)
                        break
                if pair_key in seen_pairs:
                    break
