import logging

from django.core.files.base import ContentFile
from django.utils.translation import gettext as _

from laboratory.models import Laboratory, ShelfObject, OrganizationStructure
from laboratory.report_utils import ExcelGraphBuilder
from report.utils import (
    set_format_table_columns,
    get_report_name,
    load_dataset_by_column,
    format_datetime,
)

logger = logging.getLogger("organilab")


def get_dataset_report_discard_objects(report, laboratory, column_list=None):
    dataset = []
    filters = {"shelf__discard": True, "in_where_laboratory": laboratory}
    if "period" in report.data:
        dates = report.data["period"].split("-")
        if len(dates) == 2:
            dates[0] = format_datetime(dates[0].strip(), "initial")
            dates[1] = format_datetime(dates[1].strip(), "final")
            filters.update({"creation_date__range": dates})

    shelfobjects = (
        ShelfObject.objects.filter(**filters)
        .values(
            "shelf",
            "shelf__name",
            "object__name",
            "quantity",
            "is_box",
            "quantity_units",
            "creation_date",
            "created_by__username",
            "created_by__last_name",
            "measurement_unit__description",
            "shelfobject_code",
        )
        .order_by("shelf")
    )

    for obj in shelfobjects.distinct():
        if obj["is_box"] and obj["quantity_units"]:
            total = sum(b["units"] for b in obj["quantity_units"]) * obj["quantity"]
        else:
            total = obj["quantity"]
        unit = (
            obj["measurement_unit__description"]
            if obj["measurement_unit__description"]
            else ""
        )
        data_column = {
            "shelf": obj["shelf__name"] if obj["shelf__name"] else "",
            "shelfobject_code": (
                obj["shelfobject_code"] if obj["shelfobject_code"] else ""
            ),
            "object": obj["object__name"] if obj["object__name"] else "",
            "amount": str(round(total, 3)),
            "unit": unit,
            "date": obj["creation_date"].strftime("%Y-%m-%d"),
            "created_by": (
                obj["created_by__username"]
                if obj["created_by__username"]
                else _("Unknown")
            ),
        }

        obj_item = list(data_column.values())

        if column_list:
            obj_item = load_dataset_by_column(column_list, data_column)
        dataset.append(obj_item)
    dataset.append([])
    return dataset


def report_discard_object_doc(report):
    builder = ExcelGraphBuilder()
    content = [
        _("Shelf"),
        _("Unit code"),
        _("Object"),
        _("Amount"),
        _("Unit"),
        _("Date"),
        _("Creator"),
    ]
    doc = []
    organization = OrganizationStructure.objects.filter(
        pk=report.data["organization"]
    ).first()
    labs = report.data.get("laboratory", [])
    labs = organization.get_my_laboratories if len(labs) == 0 else labs

    # El payload guarda los pks elegidos el día que se pidió el reporte, y un
    # laboratorio puede haberse borrado desde entonces. Se resuelven de una
    # consulta y los ausentes se omiten con aviso: un informe parcial sobre los
    # laboratorios que existen es útil, una excepción no. La variante HTML los
    # filtra igual, de modo que ambas dan el mismo resultado.
    laboratories = {
        lab.pk: lab for lab in Laboratory.objects.filter(pk__in=list(labs))
    }
    missing = [pk for pk in labs if pk not in laboratories]
    if missing:
        logger.warning(
            "Reporte %s: se omiten %d laboratorios que ya no existen: %s",
            report.pk,
            len(missing),
            missing,
        )

    for lab in labs:
        laboratory = laboratories.get(lab)
        if laboratory is None:
            continue

        doc += [[laboratory.name], content] + get_dataset_report_discard_objects(
            report, lab, None
        )
    total_labs = len(laboratories) * 2 + 1
    record_total = len(doc) - total_labs
    report_name = get_report_name(report)
    doc.insert(0, [report_name])
    file = builder.save_ods(doc, format_type=report.file_type)
    file_name = f"{report_name}.{report.file_type}"
    file.seek(0)
    doc = ContentFile(file.getvalue(), name=file_name)
    report.file = doc
    report.save()
    file.close()
    return record_total


def get_dataset_report_discard_objects_html(report, column_list=None):
    dataset = []
    filters = {"shelf__discard": True}
    organization = OrganizationStructure.objects.filter(
        pk=report.data["organization"]
    ).first()
    labs = report.data.get("laboratory", [])
    labs = organization.get_my_laboratories if len(labs) == 0 else labs
    if "period" in report.data:
        dates = report.data["period"].split("-")
        if len(dates) == 2:
            dates[0] = format_datetime(dates[0].strip(), "initial")
            dates[1] = format_datetime(dates[1].strip(), "final")
            filters.update({"creation_date__range": dates})

    for lab in labs:
        shelfobjects = (
            ShelfObject.objects.filter(**filters, in_where_laboratory__pk=lab)
            .values(
                "shelf",
                "shelf__name",
                "object__name",
                "quantity",
                "is_box",
                "quantity_units",
                "creation_date",
                "in_where_laboratory__name",
                "created_by__username",
                "measurement_unit__description",
                "shelfobject_code",
            )
            .order_by("shelf")
        )

        for obj in shelfobjects.distinct():
            if obj["is_box"] and obj["quantity_units"]:
                total = sum(b["units"] for b in obj["quantity_units"]) * obj["quantity"]
            else:
                total = obj["quantity"]
            unit = (
                obj["measurement_unit__description"]
                if obj["measurement_unit__description"]
                else ""
            )
            data_column = {
                "in_where_laboratory__name": obj["in_where_laboratory__name"],
                "shelf__name": obj["shelf__name"],
                "shelfobject_code": (
                    obj["shelfobject_code"] if obj["shelfobject_code"] else ""
                ),
                "object__name": obj["object__name"],
                "quantity": str(round(total, 3)),
                "measurement_unit__description": unit,
                "created_by": (
                    obj["created_by__username"]
                    if obj["created_by__username"]
                    else _("Unknown")
                ),
                "creation_date": obj["creation_date"].strftime("%Y-%m-%d"),
            }

            obj_item = list(data_column.values())

            if column_list:
                obj_item = load_dataset_by_column(column_list, data_column)
            dataset.append(obj_item)
    return dataset


def report_discard_object_html(report):

    columns_fields = [
        {"name": "in_where_laboratory__name", "title": _("Laboratory")},
        {"name": "shelf__name", "title": _("Shelf")},
        {"name": "shelfobject_code", "title": _("Unit code")},
        {"name": "object__name", "title": _("Object")},
        {"name": "quantity", "title": _("Quantity")},
        {"name": "measurement_unit__description", "title": _("Unit")},
        {"name": "created_by", "title": "User"},
        {"name": "creation_date", "title": _("Date")},
    ]

    columns_fields = set_format_table_columns(columns_fields)
    column_list = list(map(lambda x: x["name"], columns_fields))
    report.table_content = {
        "columns": columns_fields,
        "dataset": get_dataset_report_discard_objects_html(report, column_list),
    }
    report.save()
    return len(report.table_content["dataset"])
