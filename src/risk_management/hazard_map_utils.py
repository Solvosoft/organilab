import json
import logging

from laboratory.models import (
    BaseUnitValues,
    Furniture,
    LaboratoryRoom,
    Object,
    Shelf,
    ShelfObject,
)
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
        'object__sustancecharacteristics__h_code'
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

        if hasattr(obj, 'sustancecharacteristics') and obj.sustancecharacteristics:
            h_codes = list(
                obj.sustancecharacteristics.h_code.values_list('code', flat=True)
            )
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


def _parse_dataconfig_cell(cell):
    """Parse a single dataconfig cell into a list of shelf PKs (as int)."""
    if not cell:
        return []
    if isinstance(cell, int):
        return [cell]
    if isinstance(cell, str):
        parts = cell.split(",")
        result = []
        for p in parts:
            p = p.strip()
            if p:
                try:
                    result.append(int(p))
                except (ValueError, TypeError):
                    pass
        return result
    if isinstance(cell, list):
        result = []
        for item in cell:
            if isinstance(item, int):
                result.append(item)
            elif isinstance(item, str):
                try:
                    result.append(int(item.strip()))
                except (ValueError, TypeError):
                    pass
        return result
    return []


def compute_lab_tonnage(laboratory):
    """Compute total reactive weight in kg and tons for a laboratory.

    Sums ShelfObject quantities for reactives whose measurement_unit has
    a BaseUnitValues with base 'Kilogramos', converting via get_conversion_units().
    Returns {"kilograms": float, "tons": float}.
    """
    total_kg = 0.0
    shelf_objects = ShelfObject.objects.filter(
        in_where_laboratory=laboratory,
        object__type=Object.REACTIVE,
    ).select_related('measurement_unit')

    for so in shelf_objects:
        if so.measurement_unit is None or so.quantity is None:
            continue
        buv = BaseUnitValues.objects.filter(
            measurement_unit=so.measurement_unit
        ).select_related('measurement_unit_base').first()
        if buv and buv.measurement_unit_base and buv.measurement_unit_base.description == "Kilogramos":
            converted = get_conversion_units(so.measurement_unit, float(so.quantity))
            if converted is not None:
                total_kg += converted

    return {"kilograms": round(total_kg, 4), "tons": round(total_kg / 1000, 6)}


def build_lab_hazard_map(laboratory):
    """Build complete hazard map data for a laboratory.

    Returns structured dict with rooms, furniture grids, shelf colors,
    summary counts, and incompatibility alerts.
    """
    rooms_data = []
    summary = {"green": 0, "yellow": 0, "red": 0, "gray": 0}
    alerts = []

    rooms = LaboratoryRoom.objects.filter(laboratory=laboratory)

    for room in rooms:
        all_shelves_data = collect_room_shelf_hcodes(room)

        shelf_colors = {}
        for shelf_pk, sdata in all_shelves_data.items():
            compat_code, worst_pair = compute_shelf_danger(
                shelf_pk, sdata["h_codes"], all_shelves_data
            )
            color = HAZARD_COLORS.get(compat_code, HAZARD_COLORS['-'])
            shelf_colors[shelf_pk] = {
                "compat_code": compat_code,
                "color": color,
                "worst_pair": worst_pair,
                "substances": sdata["substances"],
                "name": sdata["name"],
            }

            if compat_code == 'V':
                summary["green"] += 1
            elif compat_code == 'A':
                summary["yellow"] += 1
            elif compat_code == 'R':
                summary["red"] += 1
            else:
                summary["gray"] += 1

        _collect_alerts(all_shelves_data, alerts)

        furniture_list = []
        furnitures = Furniture.objects.filter(labroom=room)

        for furniture in furnitures:
            grid = _build_furniture_grid(furniture, shelf_colors)
            furniture_list.append({
                "name": furniture.name,
                "pk": furniture.pk,
                "grid": grid,
            })

        rooms_data.append({
            "name": room.name,
            "furniture_list": furniture_list,
        })

    return {
        "laboratory": laboratory.name,
        "laboratory_pk": laboratory.pk,
        "rooms": rooms_data,
        "summary": summary,
        "alerts": alerts,
        "tonnage": compute_lab_tonnage(laboratory),
    }


def _build_furniture_grid(furniture, shelf_colors):
    """Build the grid representation for a furniture using its dataconfig."""
    grid = []
    if not furniture.dataconfig:
        shelves = Shelf.objects.filter(furniture=furniture)
        if shelves.exists():
            row_shelves = []
            for shelf in shelves:
                row_shelves.append(_shelf_to_dict(shelf, shelf_colors))
            grid.append([{"shelves": row_shelves}])
        return grid

    try:
        dataconfig = json.loads(furniture.dataconfig)
    except (json.JSONDecodeError, TypeError):
        return grid

    for row in dataconfig:
        grid_row = []
        for cell in row:
            shelf_pks = _parse_dataconfig_cell(cell)
            cell_shelves = []
            for pk in shelf_pks:
                try:
                    shelf = Shelf.objects.get(pk=pk)
                except Shelf.DoesNotExist:
                    continue
                cell_shelves.append(_shelf_to_dict(shelf, shelf_colors))
            grid_row.append({"shelves": cell_shelves})
        grid.append(grid_row)

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
