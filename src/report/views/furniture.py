from django.core.files.base import ContentFile
from django.utils.translation import gettext as _

from laboratory.report_utils import ExcelGraphBuilder
from report.utils import (
    set_format_table_columns,
    get_report_name,
    load_dataset_by_column,
)
from report.utils import get_furniture_queryset_by_filters


def get_object_type(report):
    """Tipo de objeto pedido; la cadena vacía significa «todos».

    El payload de un reporte se guarda tal como estaba el día que se pidió, así
    que puede no traer todas las claves que el código espera hoy. Un reporte
    debe poder regenerarse siempre: leer la clave directamente haría que un
    payload incompleto tumbara la tarea entera en vez de producir el informe.
    Ausencia se interpreta como «sin filtro», que es el comportamiento neutro.

    Mismo resguardo que usan `report.views.lab_room` y `report.views.objects`.
    """
    return report.data.get("object_type", "")


def get_dataset(report, column_list=None):
    dataset = []
    objects = []
    object_type = get_object_type(report)
    furniture_list = get_furniture_queryset_by_filters(report)
    for furniture in furniture_list:
        if object_type != "":
            objects = (
                furniture.get_objects()
                .filter(object__type=object_type)
                .distinct("pk")
                .order_by("pk")
            )
        else:
            objects = furniture.get_objects().distinct("pk").order_by("pk")
        for shelfobject in objects:
            shelf_unit = shelfobject.get_measurement_unit_display()
            obj_type = shelfobject.object.get_type_display()
            furniture = shelfobject.shelf.furniture
            data_column = {
                "shelfobject_code": (
                    shelfobject.shelfobject_code if shelfobject.shelfobject_code else ""
                ),
                "code": shelfobject.object.code,
                "object": shelfobject.object.name,
                "type": obj_type,
                "quantity": f"{round(shelfobject.total_quantity, 3)} {shelf_unit}",
                # `in_where_laboratory` es opcional en el modelo, así que un
                # informe no puede darlo por hecho: una celda vacía informa,
                # una excepción deja al usuario sin informe.
                "laboratory": (
                    shelfobject.in_where_laboratory.name
                    if shelfobject.in_where_laboratory
                    else ""
                ),
                "laboratory_room": furniture.labroom.name,
                "furniture": furniture.name,
                "shelf": shelfobject.shelf.name,
            }
            obj_item = list(data_column.values())

            if column_list:
                obj_item = load_dataset_by_column(column_list, data_column)
            dataset.append(obj_item)
    return dataset


def get_dataset_report_reactive(report, column_list=None):
    dataset = []
    furniture_list = get_furniture_queryset_by_filters(report)
    i = 0
    objects = []
    object_type = get_object_type(report)
    extra_filter = {
        "object__substancharacteristics_object__is_precursor": report.data.get(
            "is_precursor", False
        )
    }
    for furniture in furniture_list:
        if object_type != "":
            objects = furniture.get_objects().filter(object__type=object_type)
            if extra_filter["object__substancharacteristics_object__is_precursor"]:
                objects = objects.filter(**extra_filter)
        else:
            objects = furniture.get_objects()
        for reactive in objects.distinct("pk").order_by("pk"):
            physical = ""
            health = ""
            enviroment = ""
            cas_id = ""
            i += 1
            sga_char = reactive.object.substancharacteristics_object.first()
            if sga_char:
                physical = " ".join(
                    sga_char.h_code.filter(
                        category_h_code__danger_category="physical"
                    ).values_list("description", flat=True)
                )
                health = " ".join(
                    sga_char.h_code.filter(
                        category_h_code__danger_category="health"
                    ).values_list("description", flat=True)
                )
                enviroment = " ".join(
                    sga_char.h_code.filter(
                        category_h_code__danger_category="environment"
                    ).values_list("description", flat=True)
                )
                cas_id = reactive.object.cas_code

            location = (
                reactive.in_where_laboratory.location
                if hasattr(reactive.in_where_laboratory, "location")
                else ""
            )
            physical_status = (
                reactive.get_physical_status_display()
                if reactive.physical_status
                else ""
            )
            data_column = {
                "shelfobject_code": (
                    reactive.shelfobject_code if reactive.shelfobject_code else ""
                ),
                "name": reactive.object.name,
                "cas_id": cas_id,
                "location": location,
                "physical_status": physical_status,
                "physical": physical,
                "health": health,
                "environment": enviroment,
                "concentration": reactive.concentration,
                "quantity": round(reactive.total_quantity, 3),
                "measurement_unit": reactive.get_measurement_unit_display(),
                "laboratory_room": furniture.labroom.name,
                "furniture": furniture.name,
                "shelf": reactive.shelf.name,
            }
            obj_item = list(data_column.values())

            if column_list:
                obj_item = load_dataset_by_column(column_list, data_column)
            dataset.append(obj_item)

    return dataset


def report_reactive_html(report):
    columns_fields = [
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
        {"name": "laboratory_room", "title": _("Laboratory Room")},
        {"name": "furniture", "title": _("Furniture")},
        {"name": "shelf", "title": _("Shelf")},
    ]
    columns_fields = set_format_table_columns(columns_fields)
    column_list = list(map(lambda x: x["name"], columns_fields))
    report.table_content = {
        "columns": columns_fields,
        "dataset": get_dataset_report_reactive(report, column_list),
    }
    report.save()
    return len(report.table_content["dataset"])


def furniture_html(report):
    if get_object_type(report) != "0":
        columns_fields = [
            {"name": "shelfobject_code", "title": _("Unit code")},
            {"name": "code", "title": _("Code")},
            {"name": "object", "title": _("Object")},
            {"name": "type", "title": _("Type")},
            {"name": "quantity", "title": _("Quantity")},
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
    else:
        return report_reactive_html(report)


def report_reactive_list_doc(report):
    builder = ExcelGraphBuilder()
    content = [
        [
            _("Code"),
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
            _("Laboratory Room"),
            _("Furniture"),
            _("Shelf"),
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


def furniture_doc(report):
    if get_object_type(report) != "0":

        builder = ExcelGraphBuilder()
        content = [
            [
                _("Unit code"),
                _("Code"),
                _("Object"),
                _("Type"),
                _("Quantity"),
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
    else:
        return report_reactive_list_doc(report)
