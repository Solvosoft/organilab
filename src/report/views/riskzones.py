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
from risk_management.models import RiskZone
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
