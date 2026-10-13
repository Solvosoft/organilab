from collections import defaultdict

from django.core.files.base import ContentFile
from django.utils.timezone import now
from django.utils.translation import gettext as _
from laboratory.models import (
    ShelfObject,
    Laboratory,
    Object,
    OrganizationStructure,
)
from laboratory.report_utils import ExcelGraphBuilder
from laboratory.utils_base_unit import (
    cached_units,
    get_conversion_units,
    get_unit_info,
)
from report.utils import (
    get_report_name,
    load_dataset_by_column,
    set_format_table_columns,
)


def _stock_row(data_column, column_list):
    if column_list:
        obj_item = load_dataset_by_column(column_list, data_column)
    else:
        obj_item = list(data_column.values())
    return [("" if v is None else v) for v in obj_item]


def _converted_total(shelfobjects, quantity_of):
    """Suma de cantidades en unidad base; lo que no convierte no suma."""
    total = 0
    for shelfobj in shelfobjects:
        converted = get_conversion_units(
            shelfobj.measurement_unit_id, quantity_of(shelfobj)
        )
        if converted is not None:
            total += converted
    return total


def _base_unit_description(shelfobj):
    info = get_unit_info(shelfobj.measurement_unit_id)
    return info.base_description if info and info.base_description else ""


def _expiration(shelfobj):
    date = shelfobj.reactive_expiration_date
    return date.strftime("%d/%m/%Y") if date else ""


def _molecular_formula(obj):
    sc = obj.get_sga_characteristic()
    return sc.molecular_formula if sc and sc.molecular_formula else ""


def get_stock_dataset(lab_pk, column_list=None):
    """Una fila por (envase, reactivo) y otra por reactivo sin envase.

    Todo el inventario del laboratorio sale de una consulta y se agrupa en
    Python. Antes se consultaba por envase y por reactivo, y además se repetían
    filas: la lista de envases y la de reactivos traían un elemento por cada
    ShelfObject en vez de uno por envase o por reactivo.
    """
    dataset = []
    filters = {"object__type": Object.REACTIVE}

    if lab_pk:
        filters["in_where_laboratory__pk"] = lab_pk

    shelfobjects = (
        ShelfObject.objects.filter(**filters)
        .select_related(
            "object",
            "container__object__materialcapacity__capacity_measurement_unit",
        )
        .prefetch_related("object__substancharacteristics_object")
        .order_by("pk")
    )

    in_containers = defaultdict(lambda: defaultdict(list))
    without_container = defaultdict(list)
    for shelfobj in shelfobjects:
        if shelfobj.container_id:
            in_containers[shelfobj.container_id][shelfobj.object_id].append(shelfobj)
        else:
            without_container[shelfobj.object_id].append(shelfobj)

    with cached_units():
        for by_object in in_containers.values():
            for group in by_object.values():
                reactive = group[0]
                container_object = reactive.container
                status = ""
                if reactive.physical_status:
                    status = reactive.get_physical_status_display()
                capacity = ""
                capacity_measurement_unit = ""
                if hasattr(container_object.object, "materialcapacity"):
                    material = container_object.object.materialcapacity
                    capacity = material.capacity
                    if material.capacity_measurement_unit:
                        capacity_measurement_unit = (
                            material.capacity_measurement_unit.description
                        )
                data_column = {
                    "name": reactive.object.name,
                    "cas_id": reactive.object.cas_code,
                    "molecular_formula": _molecular_formula(reactive.object),
                    "physical_status": status,
                    "quantity": round(
                        _converted_total(group, lambda so: so.total_quantity), 3
                    ),
                    "reactive_unit": _base_unit_description(reactive),
                    "container_capacity": capacity,
                    "container_unit": capacity_measurement_unit,
                    "container_quantity": len(group),
                    "container": container_object.object.name,
                    "threshold": reactive.object.threshold,
                    "max_measurement_unit": "",
                    "expiration_date": _expiration(reactive),
                }
                dataset.append(_stock_row(data_column, column_list))

        for group in without_container.values():
            reactive = group[0]
            cas_id = ""
            molecular_formula = ""
            if reactive.object.is_pure:
                cas_id = reactive.object.cas_code
                molecular_formula = _molecular_formula(reactive.object)
            status = ""
            if reactive.physical_status:
                status = reactive.get_physical_status_display()
            amount = _converted_total(
                group,
                lambda so: so.total_quantity if not so.is_box else so.get_box_totals(),
            )
            data_column = {
                "name": reactive.object.name,
                "cas_id": cas_id,
                "molecular_formula": molecular_formula,
                "physical_status": status,
                "quantity": round(amount, 3),
                "reactive_unit": _base_unit_description(reactive),
                "container_capacity": "",
                "container_unit": "",
                "container_quantity": 0,
                "container": "",
                "threshold": reactive.object.threshold,
                "max_measurement_unit": "",
                "expiration_date": _expiration(reactive),
            }
            dataset.append(_stock_row(data_column, column_list))

    return dataset


def report_stock(report):
    builder = ExcelGraphBuilder()
    columns = [
        [
            _("Name"),
            _("CAS Number"),
            _("Molecular Formula"),
            _("Physical Status"),
            _("Quantity"),
            _("Measurement Unit"),
            _("Container Capacity"),
            _("Measurement Unit"),
            _("Container Quantity"),
            _("Container Material"),
            _("Maximum Annual Amount"),
            _("Measurement Unit"),
            _("Expiration date of the reagent"),
        ]
    ]
    content = [
        [""],
        [
            "Invetario de sustancias químicas",
            "Fecha: " + now().strftime("%d/%m/%Y"),
        ],
    ]

    laboratories = report.data.get("laboratory", [])

    if len(laboratories) == 0:
        organization = OrganizationStructure.objects.filter(
            pk=report.data["organization"]
        ).first()
        laboratories = list(set(organization.get_my_laboratories))

    for lab_id in laboratories:
        try:
            laboratory = Laboratory.objects.get(pk=lab_id)
        except Laboratory.DoesNotExist:
            continue

        headers = [
            [""],
            [""],
            [
                "Laboratorio o centro de trabajo",
                laboratory.name if laboratory.name else "N/A",
            ],
            [
                "Nombre del coordinador",
                laboratory.coordinator if laboratory.coordinator else "N/A",
            ],
            [
                "Unidad Académica o Administrativa",
                laboratory.unit if laboratory.unit else "N/A",
            ],
            ["Teléfono", laboratory.phone_number if laboratory.phone_number else "N/A"],
            ["Email", laboratory.email if laboratory.email else "N/A"],
        ]
        content += headers + columns + get_stock_dataset(lab_id, None)

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


def get_stock_cartel_dataset(report, column_list=None):
    """Cartel de inventario: una fila por unidad base, sustancia y estado físico.

    Antes era un triple bucle (unidad base × sustancia × cada estado físico
    posible) con una consulta por vuelta aunque no hubiera nada que sumar; a
    escala real no terminaba. Ahora es una consulta y una agrupación.
    """
    dataset = []
    filters = {
        "object__type": Object.REACTIVE,
    }
    organization = OrganizationStructure.objects.filter(
        pk=report.data["organization"]
    ).first()

    laboratories = report.data.get("laboratory", [])
    general = not laboratories or len(laboratories) > 1

    if general:
        filters["in_where_laboratory__pk__in"] = (
            laboratories if len(laboratories) > 1 else organization.get_my_laboratories
        )
    else:
        filters["in_where_laboratory__pk"] = laboratories[0]

    # El orden de los estados es el del modelo; «sin estado» va primero. Un
    # estado vacío o fuera de la lista nunca se reportó y sigue sin reportarse.
    status_order = {None: 0}
    for position, key in enumerate(dict(ShelfObject.PHYSICAL_STATUS), start=1):
        status_order[key] = position

    shelfobjects = (
        ShelfObject.objects.filter(**filters)
        .select_related("object", "in_where_laboratory")
        .prefetch_related(
            "object__substancharacteristics_object__storage_class"
        )
        .order_by("pk")
    )

    with cached_units() as unit_map:
        groups = defaultdict(list)
        for shelfobj in shelfobjects:
            info = unit_map.get(shelfobj.measurement_unit_id)
            if info is None or info.base_id is None:
                continue
            if shelfobj.physical_status not in status_order:
                continue
            key = (
                info.base_id,
                shelfobj.object_id,
                status_order[shelfobj.physical_status],
            )
            groups[key].append(shelfobj)

        base_names = {info.base_id: info.base_description for info in unit_map.values()}
        for key in sorted(groups):
            group = groups[key]
            shelfobj = group[0]
            status = ""
            if shelfobj.physical_status:
                status = shelfobj.get_physical_status_display()
            lab_name = (
                shelfobj.in_where_laboratory.name
                if shelfobj.in_where_laboratory
                else ""
            )
            data_column = {
                "in_where_laboratory__name": lab_name,
                "substance_name": shelfobj.object.name,
                "cas_id": shelfobj.object.cas_code,
                "quantity": round(
                    _converted_total(group, lambda so: so.total_quantity), 3
                ),
                "measurement_unit": base_names.get(key[0], ""),
                "physical_status": status,
                "storage_class": shelfobj.object.get_storage_class,
            }
            dataset.append(_stock_row(data_column, column_list))

    return dataset


def report_reactive_stock_html(report):
    columns_fields = [
        {"name": "in_where_laboratory__name", "title": _("Laboratory")},
        {"name": "substance_name", "title": _("Substance")},
        {"name": "cas_id", "title": _("CAS Number")},
        {"name": "quantity", "title": _("Quantity")},
        {"name": "measurement_unit", "title": _("Measurement Unit")},
        {"name": "physical_status", "title": _("State")},
        {"name": "storage_class", "title": _("Storage Class")},
    ]
    columns_fields = set_format_table_columns(columns_fields)
    column_list = list(map(lambda x: x["name"], columns_fields))
    report.table_content = {
        "columns": columns_fields,
        "dataset": get_stock_cartel_dataset(report, column_list),
    }
    report.save()
    return len(report.table_content["dataset"])


def report_stock_cartel(report):
    builder = ExcelGraphBuilder()
    content = [
        [
            _("Laboratory"),
            _("Substance name"),
            _("CAS Number"),
            _("Quantity"),
            _("Measurement Unit"),
            _("State"),
            _("Storage Class"),
        ]
    ]
    content = content + get_stock_cartel_dataset(report, None)
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
