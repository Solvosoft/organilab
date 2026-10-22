import copy
import json
import unicodedata
from collections import defaultdict
from io import BytesIO

from django.contrib.auth.decorators import login_required, permission_required
from django.core.files.base import ContentFile
from django.http import Http404
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext as _

from laboratory.models import (
    Laboratory,
    ShelfObject,
    Object,
    Catalog,
    OrganizationStructure,
)
from laboratory.report_utils import ExcelGraphBuilder
from laboratory.utils import check_user_access_kwargs_org
from laboratory.utils_base_unit import cached_units, get_conversion_units
from presentation.pdf import html_to_pdf
from report.datasets import hcode_threshold_map
from report.utils import (
    filter_period,
    set_format_table_columns,
    get_report_name,
    load_dataset_by_column,
)
from risk_management.compatibility_utils import (
    get_zone_substances,
    zone_reactives,
    collect_h_codes,
    build_compatibility_matrix,
    build_hcode_substance_map,
    get_h_code_compatibility,
    get_compatibility_reason,
    H_CODE_TO_CLASS,
    COMPAT_LABELS,
)
from risk_management.models import RiskZone, Buildings
from sga.models import HCodeCategory


def get_hcode_threshold(hcodes_quantity, quantity):
    """¿Supera `quantity` alguno de los umbrales (en toneladas) de los códigos H?

    Recibe los umbrales tal como los da `values_list` (números) o las categorías
    con su atributo `threshold`. Antes solo aceptaba listas, y como se le pasaba
    un `values_list` nunca evaluaba nada: el reporte decía «no supera» siempre.
    Un umbral sin definir (0 o None) no cuenta como superado.
    """
    for threshold in hcodes_quantity or []:
        threshold = getattr(threshold, "threshold", threshold)
        if threshold and (threshold * 1000) < quantity:
            return True
    return False


def get_dataset_report(report, column_list=None):
    dataset = []
    filters = {"object__type": 0}
    risk_zones = RiskZone.objects.filter(organization__pk=report.data["organization"])
    laboratories = report.data.get("laboratory", [])
    general = not laboratories or len(laboratories) > 1

    if general:
        filters["in_where_laboratory__in"] = laboratories
    else:
        filters["in_where_laboratory__pk"] = laboratories[0]

    if "risk_zone" in report.data:
        if len(report.data["risk_zone"]) > 0:
            laboratories = list(
                risk_zones.filter(pk__in=report.data["risk_zone"])
                .exclude(buildings__isnull=True)
                .values_list("buildings__laboratories", flat=True)
            )

    if "building" in report.data:
        if len(report.data["building"]) > 0:
            if len(laboratories) == 0:
                laboratories = list(
                    risk_zones.filter(
                        buildings__pk__in=report.data["building"]
                    ).values_list("buildings__laboratories", flat=True)
                )
            else:
                laboratories.extend(
                    list(
                        risk_zones.filter(
                            buildings__pk__in=report.data["building"]
                        ).values_list("buildings__laboratories", flat=True)
                    )
                )
    if (
        len(laboratories) == 0
        and len(report.data["building"]) == 0
        and len(report.data["risk_zone"]) == 0
    ):
        laboratories = risk_zones.values_list("buildings__laboratories", flat=True)
    filters.update({"in_where_laboratory__in": list(set(laboratories))})

    # Todo el inventario del reporte en una consulta; antes eran dos consultas
    # y una conversión de unidades (5 consultas más) por cada fila.
    inventory = defaultdict(list)
    lab_names = defaultdict(dict)
    rows = ShelfObject.objects.filter(**filters).values_list(
        "object_id",
        "measurement_unit_id",
        "quantity",
        "is_box",
        "quantity_units",
        "in_where_laboratory_id",
        "in_where_laboratory__name",
    )
    for object_id, unit_id, quantity, is_box, units, lab_id, lab_name in rows:
        if is_box and units:
            quantity = sum(box.get("units", 0) for box in units) * quantity
        inventory[object_id].append((unit_id, quantity))
        if lab_id is not None:
            lab_names[object_id][lab_id] = lab_name

    objs = Object.objects.filter(pk__in=list(inventory)).prefetch_related(
        "substancharacteristics_object__h_code"
    )
    threshold_map = hcode_threshold_map()

    with cached_units():
        for reactive in objs:
            dangerous = reactive.is_dangerous
            third_square = False
            third_column = ""
            cas_id = ""

            # Solo el inventario de los laboratorios del reporte: sumar el de
            # toda la base hacía superar umbrales con unidades de otras
            # organizaciones.
            total_shelfobjects = 0
            for unit_id, quantity in inventory[reactive.pk]:
                converted = get_conversion_units(unit_id, quantity)
                if converted is not None:
                    total_shelfobjects += converted

            lab_names_txt = ", ".join(
                name for _lab_id, name in sorted(lab_names[reactive.pk].items())
            )

            if dangerous:
                third_column = _("Square 3") + " "

            thresholds = {"physical": [], "health": [], "environment": []}
            sga_char = reactive.get_sga_characteristic()
            if sga_char:
                for h_code in sga_char.h_code.all():
                    for category, value in threshold_map.get(h_code.code, ()):
                        if category in thresholds:
                            thresholds[category].append(value)
                cas_id = reactive.cas_code

                if any(thresholds.values()):
                    third_square = True
                    third_column += _("Square 4")

            if (
                total_shelfobjects > (reactive.threshold * 1000)
                and reactive.is_dangerous
                and reactive.has_threshold
            ):
                threshold = _("Yes Exceeds Threshold")
            elif not dangerous and not third_square:
                third_column = _("None")
                threshold = "NA"
            else:
                threshold = _("No Exceeds Threshold")
            if third_square and threshold == _("No Exceeds Threshold"):
                if any(
                    get_hcode_threshold(values, total_shelfobjects)
                    for values in thresholds.values()
                ):
                    threshold = _("Yes Exceeds Threshold")

            data_column = {
                "in_where_laboratory__name": lab_names_txt,
                "name": reactive.name,
                "cas_id": cas_id,
                "square": third_column,
                "threshold": threshold,
            }
            obj_item = list(data_column.values())

            if column_list:
                obj_item = load_dataset_by_column(column_list, data_column)
            dataset.append(obj_item)
    return dataset


def report_risk_zone_html(report):
    columns_fields = [
        {"name": "in_where_laboratory__name", "title": _("Laboratory")},
        {"name": "name", "title": _("Substance")},
        {"name": "cas_id", "title": _("CAS")},
        {"name": "square", "title": _("Table 4, 3 or none")},
        {"name": "threshold", "title": _("Threshold")},
    ]

    columns_fields = set_format_table_columns(columns_fields)
    column_list = list(map(lambda x: x["name"], columns_fields))
    report.table_content = {
        "columns": columns_fields,
        "dataset": get_dataset_report(report, column_list),
    }
    report.save()
    return len(report.table_content["dataset"])


def report_risk_zone_list_doc(report):
    builder = ExcelGraphBuilder()
    content = [
        [
            _("Laboratory"),
            _("Substance"),
            _("CAS"),
            _("Table 4, 3 or none"),
            _("Exceeds THRESHOLD OR NA, if the previous (column) is none"),
        ]
    ]

    content = content + get_dataset_report(report)

    record_total = len(content) - 1
    report_name = get_report_name(report)
    content.insert(0, [report_name])
    file = builder.save_ods(content, format_type=report.file_type)

    file_name = f"{report_name}.{report.file_type}"
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.save()
    file.close()
    return record_total


def _get_compatibility_buildings(report):
    """Return filtered buildings queryset and risk_zone pks from report data."""
    org_pk = report.data.get("organization") or report.data.get("org_pk")
    buildings_qs = Buildings.objects.filter(organization_id=org_pk)

    risk_zones = report.data.get("risk_zone", [])
    buildings_filter = report.data.get("building", [])

    if buildings_filter:
        buildings_qs = buildings_qs.filter(pk__in=buildings_filter)
    elif risk_zones:
        building_pks = list(
            RiskZone.objects.filter(pk__in=risk_zones).values_list(
                "buildings", flat=True
            )
        )
        buildings_qs = buildings_qs.filter(pk__in=building_pks)

    return buildings_qs, risk_zones


def report_compatibility_html(report):
    """Generate HTML (DataTables) compatibility report with flat per-pair rows."""
    columns_fields = [
        {"name": "building", "title": _("Building")},
        {"name": "zone", "title": _("Risk Zone")},
        {"name": "h_code_a", "title": _("H-Code A")},
        {"name": "h_code_b", "title": _("H-Code B")},
        {"name": "compatibility", "title": _("Compatibility")},
        {"name": "reason", "title": _("Reason")},
        {"name": "substances_a", "title": _("Substances A")},
        {"name": "substances_b", "title": _("Substances B")},
        {"name": "laboratory_a", "title": _("Laboratory A")},
        {"name": "shelf_a", "title": _("Shelf A")},
        {"name": "laboratory_b", "title": _("Laboratory B")},
        {"name": "shelf_b", "title": _("Shelf B")},
    ]

    columns_fields = set_format_table_columns(columns_fields)
    column_list = list(map(lambda x: x["name"], columns_fields))

    dataset = []
    buildings_qs, risk_zones = _get_compatibility_buildings(report)
    risk_zone_pks = risk_zones if risk_zones else None

    for building in buildings_qs:
        zones = RiskZone.objects.filter(buildings=building)
        for zone in zones:
            if risk_zone_pks and zone.pk not in risk_zone_pks:
                continue

            # Una sola lectura del inventario de la zona para las dos vistas
            # que necesita la tabla.
            reactives = zone_reactives(zone)
            lab_substances = get_zone_substances(zone, reactives)
            if not lab_substances:
                continue

            all_h_codes = collect_h_codes(lab_substances)
            if len(all_h_codes) < 2:
                continue

            hcode_map = build_hcode_substance_map(zone, reactives)

            for i, code_a in enumerate(all_h_codes):
                for code_b in all_h_codes[i + 1:]:
                    compat = get_h_code_compatibility(code_a, code_b)
                    compat_label = COMPAT_LABELS.get(compat, compat)

                    reason = ""
                    if compat == "R":
                        class_a = H_CODE_TO_CLASS.get(code_a, "")
                        class_b = H_CODE_TO_CLASS.get(code_b, "")
                        if class_a and class_b:
                            reason = get_compatibility_reason(class_a, class_b)

                    entries_a = hcode_map.get(code_a, [])
                    entries_b = hcode_map.get(code_b, [])

                    data_column = {
                        "building": building.name,
                        "zone": zone.name,
                        "h_code_a": code_a,
                        "h_code_b": code_b,
                        "compatibility": compat_label,
                        "reason": reason,
                        "substances_a": "; ".join(e["substance"] for e in entries_a),
                        "substances_b": "; ".join(e["substance"] for e in entries_b),
                        "laboratory_a": "; ".join(
                            sorted(set(e["lab"] for e in entries_a))
                        ),
                        "shelf_a": "; ".join(
                            sorted(set(e["shelf"] for e in entries_a if e["shelf"]))
                        ),
                        "laboratory_b": "; ".join(
                            sorted(set(e["lab"] for e in entries_b))
                        ),
                        "shelf_b": "; ".join(
                            sorted(set(e["shelf"] for e in entries_b if e["shelf"]))
                        ),
                    }

                    # `column_list` sale de las columnas fijas de arriba: nunca
                    # está vacía, así que no hace falta la rama sin columnas.
                    dataset.append(load_dataset_by_column(column_list, data_column))

    if not dataset:
        diag = _build_compatibility_diagnostic(buildings_qs, risk_zones)
        report.table_content = {
            "columns": columns_fields,
            "dataset": dataset,
            "diagnostic": diag,
        }
    else:
        report.table_content = {
            "columns": columns_fields,
            "dataset": dataset,
        }
    report.save()
    return len(dataset)


def _build_compatibility_diagnostic(buildings_qs, risk_zone_pks):
    """Build a diagnostic dict explaining why the compatibility table is empty."""
    total_buildings = buildings_qs.count()
    if total_buildings == 0:
        return {
            "message": _("No buildings found for this organization."),
            "detail": _("Create buildings and assign them to risk zones first."),
        }

    total_zones = 0
    total_labs = 0
    total_reactives = 0
    total_with_h_codes = 0
    unique_h_codes = set()

    for building in buildings_qs:
        zones = RiskZone.objects.filter(buildings=building)
        for zone in zones:
            if risk_zone_pks and zone.pk not in risk_zone_pks:
                continue
            total_zones += 1
            labs = zone.laboratories.all()
            total_labs += labs.count()
            for lab in labs:
                shelf_objects = (
                    ShelfObject.objects.filter(
                        in_where_laboratory=lab, object__type=Object.REACTIVE
                    )
                    .select_related("object")
                    .prefetch_related("object__substancharacteristics_object__h_code")
                )
                total_reactives += shelf_objects.count()
                for so in shelf_objects:
                    sga_char = so.object.get_sga_characteristic()
                    if sga_char:
                        h_codes = [h_code.code for h_code in sga_char.h_code.all()]
                        if h_codes:
                            total_with_h_codes += 1
                            unique_h_codes.update(h_codes)

    if total_zones == 0:
        msg = _("No risk zones found linked to the selected buildings.")
        detail = _("Assign risk zones to buildings first.")
    elif total_labs == 0:
        msg = _("Risk zones found but none have laboratories assigned.")
        detail = _("Assign laboratories to the risk zones.")
    elif total_reactives == 0:
        msg = _("Laboratories found but no reactive substances registered.")
        detail = _(
            "Register reactive substances (ShelfObjects of type Reactive) in the laboratories."
        )
    elif total_with_h_codes == 0:
        msg = _(
            "Reactive substances found but none have H-codes (danger indications) assigned."
        )
        detail = _(
            "Edit each reactive substance and assign H-codes via Substance Characteristics (SGA)."
        )
    elif len(unique_h_codes) < 2:
        msg = _(
            "Only one unique H-code found across all zones. At least 2 different H-codes are needed to compare compatibility."
        )
        detail = _("Assign different H-codes to the reactive substances.")
    else:
        msg = _(
            "No compatibility pairs generated. Each zone needs at least 2 different H-codes within the same zone."
        )
        detail = _(
            "Ensure at least one risk zone contains substances with 2 or more different H-codes."
        )

    return {
        "message": str(msg),
        "detail": str(detail),
        "stats": {
            "buildings": total_buildings,
            "risk_zones": total_zones,
            "laboratories": total_labs,
            "reactives": total_reactives,
            "reactives_with_h_codes": total_with_h_codes,
            "unique_h_codes": len(unique_h_codes),
        },
    }


def report_compatibility_ods(report):
    """Generate ODS compatibility matrix report."""
    import logging
    from risk_management.compatibility_utils import generate_compatibility_ods

    logger = logging.getLogger("organilab.report")

    buildings_qs, risk_zones = _get_compatibility_buildings(report)

    file_io = generate_compatibility_ods(
        buildings_qs, risk_zone_pks=risk_zones if risk_zones else None
    )

    report_name = report.data.get("name", "compatibility_report")
    file_io.seek(0)
    report.file = ContentFile(file_io.getvalue(), name="%s.ods" % report_name)
    report.save()
    return buildings_qs.count()


def report_hazard_map_html(report):
    """Generate HTML hazard map report data for laboratories."""
    from risk_management.hazard_map_utils import build_lab_hazard_map

    org_pk = report.data.get("organization") or report.data.get("org_pk")
    lab_pks = report.data.get("laboratory", [])
    org_pk = OrganizationStructure.objects.filter(pk=org_pk).first()
    labs = list(set(org_pk.get_my_laboratories))
    if lab_pks:
        labs = lab_pks
    labs = Laboratory.objects.filter(pk__in=labs)

    map_data = []
    for lab in labs:
        lab_map = build_lab_hazard_map(lab)
        map_data.append(lab_map)

    report.table_content = {"map_data": map_data}
    report.save()
    return len(map_data)


def _sort_key_without_accents(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()


def _pdf_substances_text(substances, no_density=()):
    """Sustancias de un estante en un solo párrafo, para el PDF.

    Una por línea, un estante lleno ocupa más que una página y xhtml2pdf no
    parte una celda de tabla: el PDF entero fallaba. Sin repetidos (varias
    unidades del mismo reactivo) y separadas por «; » porque cada una ya
    lleva comas en sus códigos H.
    """
    mark = format_html(' <span class="no-density">({})</span>', _("No density"))
    return format_html_join(
        "; ",
        "{}{}",
        (
            (substance, mark if substance in no_density else "")
            for substance in sorted(set(substances), key=_sort_key_without_accents)
        ),
    )


COMPATIBILITY_PDF_SUBSTANCES = ("substances_a", "substances_b")
COMPATIBILITY_PDF_MAX_CHARS = 1200


def _split_substances(text, max_chars=COMPATIBILITY_PDF_MAX_CHARS):
    items = sorted(
        {item.strip() for item in str(text or "").split("; ") if item.strip()},
        key=_sort_key_without_accents,
    )
    chunks, current = [], []
    for item in items:
        if current and len("; ".join(current + [item])) > max_chars:
            chunks.append("; ".join(current))
            current = []
        current.append(item)
    if current:
        chunks.append("; ".join(current))
    return chunks or [""]


def compatibility_pdf_table(table_content):
    """Copia de la tabla de compatibilidad para el PDF.

    xhtml2pdf no parte una fila entre páginas: una lista de sustancias que no
    cabe se reparte en filas consecutivas del mismo par, sin perder ninguna.
    """
    columns = copy.deepcopy(table_content["columns"])
    names = [column.get("name") for column in columns]
    positions = [names.index(name) for name in COMPATIBILITY_PDF_SUBSTANCES if name in names]
    dataset, items = [], []
    for number, row in enumerate(table_content["dataset"], start=1):
        parts = {i: _split_substances(row[i]) for i in positions}
        total = max([len(chunks) for chunks in parts.values()] + [1])
        for index in range(total):
            new_row = list(row)
            for i, chunks in parts.items():
                new_row[i] = chunks[index] if index < len(chunks) else ""
                if len(chunks) > 1 and index < len(chunks):
                    new_row[i] = "%s %s" % (
                        new_row[i],
                        _("(%(part)s of %(total)s)") % {"part": index + 1, "total": len(chunks)},
                    )
            dataset.append(new_row)
            items.append(number)
    return {"columns": columns, "dataset": dataset, "items": items}


def _hazard_map_pdf_data(map_data):
    """Copia de ``map_data`` con el texto de sustancias de cada estante.

    Es una copia: ``table_content`` se guarda y lo usa también la vista web,
    que sigue mostrando una sustancia por línea.
    """
    map_data = copy.deepcopy(map_data)
    for lab_data in map_data:
        for room in lab_data.get("rooms", []):
            for furniture in room.get("furniture_list", []):
                for row in furniture.get("grid") or []:
                    for cell in row:
                        for shelf in cell.get("shelves", []):
                            shelf["substances_text"] = _pdf_substances_text(
                                shelf.get("substances", []), set(shelf.get("no_density", []))
                            )
    return map_data


def report_hazard_map_pdf(report, uri):
    """Generate PDF hazard map report."""
    map_data = _hazard_map_pdf_data(report.table_content.get("map_data", []))
    report_name = get_report_name(report)
    title = report.data.get("title", report_name)

    context = {
        "map_data": map_data,
        "user": report.created_by,
        "title": title,
        "datetime": timezone.now(),
    }

    html = render_to_string("report/hazard_map_pdf.html", context=context)
    file = BytesIO()
    html_to_pdf(html, base_url=uri, output=file)
    file_name = "%s.pdf" % report_name
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.save()
    file.close()
    return len(map_data)


@login_required
@permission_required("laboratory.view_report", raise_exception=True)
def hazard_map_visual_view(request, org_pk):
    """Direct HTML view for hazard map (bypasses Celery)."""
    from risk_management.hazard_map_utils import build_lab_hazard_map

    if not check_user_access_kwargs_org(org_pk, request.user):
        raise Http404()
    lab_pks = [pk for pk in request.GET.getlist("laboratory") if pk.isdigit()]
    title = request.GET.get("title", _("Compatibility Laboratory Report"))
    org_pk = OrganizationStructure.objects.filter(pk=org_pk).first()
    # Los pks de la query string se cruzan con los laboratorios de la
    # organización: sin esto se podía ver el mapa de un laboratorio ajeno.
    labs = Laboratory.objects.filter(pk__in=list(set(org_pk.get_my_laboratories)))
    if lab_pks:
        labs = labs.filter(pk__in=lab_pks)

    if not labs.exists():
        raise Http404()

    map_data = []
    for lab in labs:
        map_data.append(build_lab_hazard_map(lab))

    context = {
        "map_data": map_data,
        "title": title,
        "org_pk": org_pk.pk,
    }
    return render(request, "report/hazard_map_visual.html", context)
