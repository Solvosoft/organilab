from laboratory.models import ShelfObject, Object
from laboratory.report_utils import ExcelGraphBuilder
from report.utils import (
    load_dataset_by_column,
    get_report_name,
    set_format_table_columns,
)
from django.core.files.base import ContentFile
from django.utils.translation import gettext as _


def get_dataset(report, column_list=None):
    dataset = []
    filters = {
        "was_donated": True,
    }
    organization = report.data["organization"]
    if "laboratory" in report.data:
        filters["in_where_laboratory__pk__in"] = (
            report.data["laboratory"]
            if len(report.data["laboratory"]) > 0
            else organization.get_my_laboratories
        )

    shelf_objects = ShelfObject.objects.filter(**filters)

    object_type = dict(Object.TYPE_CHOICES)
    for shelfobject in shelf_objects:
        furniture = shelfobject.shelf.furniture
        if shelfobject.is_box and shelfobject.quantity_units:
            quantity = len(shelfobject.quantity_units)
            units_per_box = sum(b["units"] for b in shelfobject.quantity_units)
            shelf_unit = _("(%(units)s) units per box") % {"units": units_per_box}
            name = _("Box of %(name)s (%(quantity)s %(unit)s)") % {
                "name": shelfobject.object.name,
                "quantity": shelfobject.quantity,
                "unit": str(shelfobject.measurement_unit),
            }
        else:
            quantity = shelfobject.quantity
            shelf_unit = shelfobject.get_measurement_unit_display()
            name = shelfobject.object.name
        data_column = {
            "shelfobject_code": (
                shelfobject.shelfobject_code if shelfobject.shelfobject_code else ""
            ),
            "code": shelfobject.object.code,
            "type": str(object_type[shelfobject.object.type]),
            "status": shelfobject.status.description if shelfobject.status else "",
            "object": name,
            "quantity": round(quantity, 3),
            "unit": shelf_unit,
            "laboratory": shelfobject.in_where_laboratory.name,
            "laboratory_room": furniture.labroom.name,
            "furniture": furniture.name,
            "shelf": shelfobject.shelf.name,
        }
        obj_item = list(data_column.values())
        if column_list:
            obj_item = load_dataset_by_column(column_list, data_column)
        dataset.append(obj_item)

    return dataset


def report_donations_doc(report):
    builder = ExcelGraphBuilder()
    content = [
        [
            _("Unit code"),
            _("Code"),
            _("Type"),
            _("Status"),
            _("Object"),
            _("Quantity"),
            _("Measurement Unit"),
            _("Laboratory"),
            _("Laboratory Room"),
            _("Furniture"),
            _("Shelf"),
        ]
    ]
    content = content + get_dataset(report, None)
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


def report_donations_html(report):
    columns_fields = [
        {"name": "shelfobject_code", "title": _("Unit code")},
        {"name": "code", "title": _("Code")},
        {"name": "type", "title": _("Type")},
        {"name": "status", "title": _("Status")},
        {"name": "object", "title": _("Object")},
        {"name": "quantity", "title": _("Quantity")},
        {"name": "unit", "title": _("Measurement Unit")},
        {"name": "laboratory", "title": _("Laboratory")},
        {"name": "laboratory_room", "title": _("Laboratory Room")},
        {"name": "furniture", "title": _("Furniture")},
        {"name": "shelf", "title": _("Shelf")},
    ]
    columns_fields = set_format_table_columns(columns_fields)
    column_list = list(map(lambda x: x["name"], columns_fields))
    report.table_content = {
        "columns": columns_fields,
        "dataset": get_dataset(report, column_list),
    }
    report.save()
    return len(report.table_content["dataset"])
