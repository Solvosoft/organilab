from django.core.files.base import ContentFile
from django.utils.translation import gettext as _
from laboratory.models import ShelfObject, OrganizationStructure
from laboratory.report_utils import ExcelGraphBuilder
from report.datasets import hcode_category_map, reactive_columns
from report.utils import (
    set_format_table_columns,
    get_report_name,
    load_dataset_by_column,
)


def get_dataset_report_reactive(report, column_list=None):
    dataset = []
    filters = {"object__type": 0}

    laboratories = report.data.get("laboratory", [])
    general = not laboratories or len(laboratories) > 1
    organization = OrganizationStructure.objects.filter(
        pk=report.data["organization"]
    ).first()

    if general:
        filters["in_where_laboratory__pk__in"] = (
            laboratories if len(laboratories) > 1 else organization.get_my_laboratories
        )
    else:
        filters["in_where_laboratory__pk"] = laboratories[0]

    objs = ShelfObject.objects.for_report().filter(**filters).order_by("pk")
    category_map = hcode_category_map()
    for reactive in objs:
        lab_name = (
            reactive.in_where_laboratory.name if reactive.in_where_laboratory else ""
        )
        data_column = {"in_where_laboratory__name": lab_name}
        data_column.update(reactive_columns(reactive, category_map))
        obj_item = list(data_column.values())

        if column_list:
            obj_item = load_dataset_by_column(column_list, data_column)
        dataset.append(obj_item)
    return dataset


def report_reactive_html(report):
    columns_fields = [
        {"name": "in_where_laboratory__name", "title": _("Laboratory")},
        {"name": "shelfobject_code", "title": _("Unit code")},
        {"name": "name", "title": _("Name")},
        {"name": "cas_id", "title": _("CAS")},
        {"name": "location", "title": _("Location")},
        {"name": "physical_status", "title": _("Physical Status")},
        {"name": "physical", "title": _("Physical Hazard Category (Code H)")},
        {"name": "health", "title": _("Health Hazard Category (Code H)")},
        {"name": "environment", "title": _("Environmental Hazard Category (Code H)")},
        {"name": "concentration", "title": _("Concentration")},
        {"name": "quantity", "title": _("Quantity")},
        {"name": "measurement_unit", "title": _("Measurement Unit")},
    ]
    columns_fields = set_format_table_columns(columns_fields)
    column_list = list(map(lambda x: x["name"], columns_fields))
    report.table_content = {
        "columns": columns_fields,
        "dataset": get_dataset_report_reactive(report, column_list),
    }
    report.save()
    return len(report.table_content["dataset"])


def report_reactive_list_doc(report):
    builder = ExcelGraphBuilder()
    content = [
        [
            _("Laboratory"),
            _("Unit code"),
            _("Name"),
            _("CAS"),
            _("Location"),
            _("Physical Status"),
            _("Physical Hazard Category (Code H)"),
            _("Health Hazard Category (Code H)"),
            _("Environmental Hazard Category (Code H)"),
            _("Concentration"),
            _("Quantity"),
            _("Measurement Unit"),
        ]
    ]

    content = content + get_dataset_report_reactive(report, None)

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
