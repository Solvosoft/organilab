from django.core.files.base import ContentFile
from django.utils.translation import gettext as _
from laboratory.models import ShelfObject, Object, Catalog
from laboratory.report_utils import ExcelGraphBuilder
from laboratory.utils_base_unit import get_conversion_units
from report.utils import (
    filter_period,
    set_format_table_columns,
    get_report_name,
    load_dataset_by_column,
    get_danger_categories,
    get_conversion_units_to_kilograms,
)
from risk_management.compatibility_utils import (
    get_zone_substances,
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
    result = False
    if isinstance(hcodes_quantity, list):
        for hcode in hcodes_quantity:
            if (hcode.threshold * 1000) < quantity:
                return True
    return result


def get_dataset_report_x(report, column_list=None):

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

    objsx = ShelfObject.objects.filter(**filters)
    objs = Object.objects.filter(
        pk__in=objs.values_list("object__pk", flat=True),
        has_threshold=True,
        is_dangerous=True,
        threshold__isnull=False,
    ).distinct()
    units = Catalog.objects.filter(
        pk__in=objsx.values_list("measurement_unit", flat=True)
    )
    third_list = []
    fourth_list = []
    for reactive in objs:
        reactive_list = []

        third_square = False
        total_shelfobjects = 0
        reactive_list.append(reactive.name)
        for unit in units:
            shelfobjects = ShelfObject.objects.filter(
                object=reactive, measurement_unit=unit
            ).distinct()
            if shelfobjects.count() > 0:
                total_shelfobjects += sum(
                    [
                        get_conversion_units_to_kilograms(
                            obj.measurement_unit, obj.quantity
                        )
                        for obj in shelfobjects
                    ]
                )
        # list 3
        reactive_list.append(reactive.threshold)
        reactive_list.append(total_shelfobjects)
        reactive_list.append(_("No Exceeds Threshold"))

        if reactive.threshold * 1000 < total_shelfobjects:
            reactive_list[-1] = _("Yes Exceeds Threshold")
            third_square = True
        third_list.append(reactive_list)

        if not third_square and hasattr(reactive, "sustancecharacteristics"):
            # list 4
            danger_categories_list = get_danger_categories(reactive, total_shelfobjects)
            if len(danger_categories_list) > 0:
                if danger_categories_list[-1].threshold * 1000 < total_shelfobjects:
                    danger_categories_list.append(_("Yes Exceeds Threshold"))
                else:
                    danger_categories_list.append(_("No Exceeds Threshold"))
                fourth_list.extend(danger_categories_list)
    total_fifth_list = {
        "enviroment": {"substance": 0, "category_threshold": 0, "total": 0},
        "health": {"substance": 0, "category_threshold": 0, "total": 0},
        "physical": {"substance": 0, "category_threshold": 0, "total": 0},
    }
    if len(fourth_list) > 0:
        for danger in fourth_list:
            total_fifth_list[danger[2]]["substance"] += danger[3]
            total_fifth_list[danger[2]]["category_threshold"] += danger[4]
            try:
                total_fifth_list[danger[2]]["total"] += danger[3] / danger[4]
            except ZeroDivisionError:
                total_fifth_list[danger[2]]["total"] = 0

        for danger in total_fifth_list:
            total_fifth_list[danger]["category_threshold"] /= 1000

    context = {
        "total_fifth_list": total_fifth_list,
        "third_list": third_list,
        "fourth_list": fourth_list,
    }
    return context


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

    objs = ShelfObject.objects.filter(**filters).values_list("object__pk", flat=True)
    objs = Object.objects.filter(pk__in=objs).distinct()

    for reactive in objs:
        cas_id = ""
        threshold = "NA"
        dangerous = reactive.is_dangerous
        third_square = False
        third_column = ""

        shelfobjects = ShelfObject.objects.filter(object=reactive).distinct()
        total_shelfobjects = sum(
            [
                get_conversion_units(obj.measurement_unit, obj.quantity)
                for obj in shelfobjects
            ]
        )

        total_health = False
        total_physical = False
        total_enviroment = False

        lab_names_txt = ", ".join(
            ShelfObject.objects.filter(**filters, object=reactive)
            .exclude(in_where_laboratory__isnull=True)
            .order_by("in_where_laboratory_id")
            .distinct("in_where_laboratory_id")
            .values_list("in_where_laboratory__name", flat=True)
        )

        if dangerous:
            third_column = _("Square 3") + " "

        if hasattr(reactive, "sustancecharacteristics"):
            physical = reactive.sustancecharacteristics.h_code.filter(
                category_h_code__danger_category="physical"
            ).values_list("description", flat=True)
            health = reactive.sustancecharacteristics.h_code.filter(
                category_h_code__danger_category="health"
            ).values_list("description", flat=True)
            enviroment = reactive.sustancecharacteristics.h_code.filter(
                category_h_code__danger_category="environment"
            ).values_list("description", flat=True)
            total_physical = reactive.sustancecharacteristics.h_code.filter(
                category_h_code__danger_category="physical"
            ).values_list("category_h_code__threshold", flat=True)
            total_health = reactive.sustancecharacteristics.h_code.filter(
                category_h_code__danger_category="health"
            ).values_list("category_h_code__threshold", flat=True)
            total_enviroment = reactive.sustancecharacteristics.h_code.filter(
                category_h_code__danger_category="environment"
            ).values_list("category_h_code__threshold", flat=True)
            cas_id = reactive.cas_code

            if physical.exists() or health.exists() or enviroment.exists():
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
            if (
                get_hcode_threshold(total_physical, total_shelfobjects)
                or get_hcode_threshold(total_health, total_shelfobjects)
                or get_hcode_threshold(total_enviroment, total_shelfobjects)
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
            RiskZone.objects.filter(
                pk__in=risk_zones
            ).values_list("buildings", flat=True)
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

            lab_substances = get_zone_substances(zone)
            if not lab_substances:
                continue

            all_h_codes = collect_h_codes(lab_substances)
            if len(all_h_codes) < 2:
                continue

            hcode_map = build_hcode_substance_map(zone)

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
                        "laboratory_a": "; ".join(sorted(set(e["lab"] for e in entries_a))),
                        "shelf_a": "; ".join(sorted(set(e["shelf"] for e in entries_a if e["shelf"]))),
                        "laboratory_b": "; ".join(sorted(set(e["lab"] for e in entries_b))),
                        "shelf_b": "; ".join(sorted(set(e["shelf"] for e in entries_b if e["shelf"]))),
                    }

                    if column_list:
                        obj_item = load_dataset_by_column(column_list, data_column)
                    else:
                        obj_item = list(data_column.values())
                    dataset.append(obj_item)

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
                shelf_objects = ShelfObject.objects.filter(
                    in_where_laboratory=lab,
                    object__type=Object.REACTIVE
                ).select_related('object').prefetch_related(
                    'object__sustancecharacteristics__h_code'
                )
                total_reactives += shelf_objects.count()
                for so in shelf_objects:
                    obj = so.object
                    if hasattr(obj, 'sustancecharacteristics') and obj.sustancecharacteristics:
                        h_codes = list(
                            obj.sustancecharacteristics.h_code.values_list('code', flat=True)
                        )
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
        detail = _("Register reactive substances (ShelfObjects of type Reactive) in the laboratories.")
    elif total_with_h_codes == 0:
        msg = _("Reactive substances found but none have H-codes (danger indications) assigned.")
        detail = _("Edit each reactive substance and assign H-codes via Substance Characteristics (SGA).")
    elif len(unique_h_codes) < 2:
        msg = _("Only one unique H-code found across all zones. At least 2 different H-codes are needed to compare compatibility.")
        detail = _("Assign different H-codes to the reactive substances.")
    else:
        msg = _("No compatibility pairs generated. Each zone needs at least 2 different H-codes within the same zone.")
        detail = _("Ensure at least one risk zone contains substances with 2 or more different H-codes.")

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
