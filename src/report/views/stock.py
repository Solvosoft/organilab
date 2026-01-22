from django.core.files.base import ContentFile
from django.utils.timezone import now
from django.utils.translation import gettext as _
from laboratory.models import ShelfObject, Laboratory, BaseUnitValues, Object, Catalog
from laboratory.report_utils import ExcelGraphBuilder
from laboratory.utils_base_unit import get_conversion_units
from report.utils import (
    get_report_name,
    load_dataset_by_column, set_format_table_columns,
)


def get_stock_dataset(report, column_list=None):
    dataset = []
    filters = {"object__type": Object.REACTIVE}
    reactive_filters = dict()
    if "lab_pk" in report.data:
        filters["in_where_laboratory__pk"] = report.data["lab_pk"]
        reactive_filters["in_where_laboratory__pk"] = report.data["lab_pk"]
    objs = (
        ShelfObject.objects.filter(**filters)
        .distinct("pk")
        .values_list("object__pk", flat=True)
    )

    object_no_containers = (
        ShelfObject.objects.filter(**filters, container__isnull=True)
        .distinct("pk")
        .values_list("object__pk", flat=True)
    )
    containers = (
        ShelfObject.objects.filter(**filters, container__isnull=False)
        .distinct("pk")
        .values_list("container__pk", flat=True)
    )
    containers = ShelfObject.objects.filter(container__pk__in=containers).values_list("container__pk", flat=True)
    reactives = []
    for container in containers:
        objs = (
            ShelfObject.objects.filter(**filters,
                                       container__pk=container)
            .distinct("pk")
            .values_list("object__pk", flat=True)
        )
        container_object = ShelfObject.objects.filter(pk=container).first()
        for obj in set(objs):

            data_column = {}
            shelfobjects = ShelfObject.objects.filter(
                container__pk=container, object__pk=obj, **reactive_filters
            ).distinct("pk")
            if shelfobjects.count() > 0:
                reactive = shelfobjects.first()

                amount = sum(
                    [
                        get_conversion_units(shelfobj.measurement_unit, shelfobj.quantity)
                        for shelfobj in shelfobjects
                    ]
                )
                # if reactive.object.is_pure:
                cas_id = reactive.object.cas_code
                molecular_formula = (
                    reactive.object.sustancecharacteristics.molecular_formula
                )
                expiration_date = reactive.reactive_expiration_date
                if expiration_date:
                    expiration_date = expiration_date.strftime("%d/%m/%Y")
                else:
                    expiration_date = ""
                status = ""
                if reactive.physical_status:
                    status = reactive.get_physical_status_display()
                base_unit = ""
                if reactive.measurement_unit:
                    base_unit = BaseUnitValues.objects.get(
                        measurement_unit=reactive.measurement_unit
                    ).measurement_unit_base.description
                capacity = ""
                capacity_measurement_unit = ""
                if hasattr(container_object.object, "materialcapacity"):
                    capacity = container_object.object.materialcapacity.capacity
                    capacity_measurement_unit = (
                        container_object.object.materialcapacity.capacity_measurement_unit.description
                    )
                data_column = {
                    "name": reactive.object.name,
                    "cas_id": cas_id,
                    "molecular_formula": molecular_formula,
                    "physical_status": status,
                    "quantity": amount,
                    "reactive_unit": base_unit,
                    "container_capacity": capacity,
                    "container_unit": capacity_measurement_unit,
                    "container_quantity": shelfobjects.count(),
                    "container": container_object.object.name,
                    "threshold": reactive.object.threshold,
                    "max_measurement_unit": "",
                    "expiration_date": expiration_date,
                }
            obj_item = list(data_column.values())

            if column_list:
                obj_item = load_dataset_by_column(column_list, data_column)
            if len(obj_item) > 0:
                dataset.append(obj_item)

    for obj in object_no_containers:
        data_column = {}
        reactive = ShelfObject.objects.filter(
            object__pk=obj, container__isnull=True
        ).first()
        amount = sum(
            [
                get_conversion_units(shelfobj.measurement_unit, shelfobj.quantity)
                for shelfobj in ShelfObject.objects.filter(
                    object__pk=obj, container__isnull=True
                ).distinct("pk")
            ]
        )

        cas_id = ""
        molecular_formula = ""

        if reactive.object.is_pure:
            cas_id = reactive.object.cas_code
            molecular_formula = reactive.object.molecular_formula
        expiration_date = reactive.reactive_expiration_date
        if expiration_date:
            expiration_date = expiration_date.strftime("%d/%m/%Y")
        else:
            expiration_date = ""
        status = ""
        if reactive.physical_status:
            status = reactive.get_physical_status_display()
        base_unit = ""
        if reactive.measurement_unit:
            base_unit = BaseUnitValues.objects.get(
                measurement_unit=reactive.measurement_unit
            ).measurement_unit_base.description
        data_column = {
            "name": reactive.object.name,
            "cas_id": cas_id,
            "molecular_formula": molecular_formula,
            "physical_status": status,
            "quantity": amount,
            "reactive_unit": base_unit,
            "container_capacity": "",
            "container_unit": "",
            "container_quantity": 0,
            "container": "",
            "threshold": reactive.object.threshold,
            "max_measurement_unit": "",
            "expiration_date": expiration_date,
        }
        obj_item = list(data_column.values())

        if column_list:
            obj_item = load_dataset_by_column(column_list, data_column)
        if len(obj_item) > 0:
            dataset.append(obj_item)

    return dataset


def report_stock(report):
    builder = ExcelGraphBuilder()
    content = [
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
    laboratory = Laboratory.objects.get(pk=report.data["lab_pk"])
    headers = [
        [
            "",
            "Invetario de sustancias químicas",
            "Fecha: " + now().strftime("%d/%m/%Y"),
        ],
        ["Datos del usuario"],
        [
            "Nombre del coordinador",
            laboratory.coordinator,
            "Laboratorio o centro de trabajo",
            laboratory.name,
            "Unidad Académica o Administrativa",
            laboratory.unit,
        ],
        ["Teléfono", laboratory.phone_number, "Email", laboratory.email],
    ]
    content = headers + content + get_stock_dataset(report, None)
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
    dataset = []
    filters = {
        "object__type": Object.REACTIVE,
        "in_where_laboratory__organization__pk": report.data["organization"]
               }
    reactive_filters = dict()
    if "laboratory" in report.data:
        if len(report.data["laboratory"]) > 0:
            filters["in_where_laboratory__pk__in"] = report.data["laboratory"]
            reactive_filters["in_where_laboratory__pk__in"] = report.data["laboratory"]
            del filters["in_where_laboratory__organization__pk"]

    objs = (
        ShelfObject.objects.filter(**filters)
        .distinct("pk")
    )
    units = Catalog.objects.filter(pk__in=objs.values_list("measurement_unit", flat=True))
    base_units = BaseUnitValues.objects.filter(measurement_unit__in=units).values_list("measurement_unit_base", flat=True)
    physical_status_list = list(dict(ShelfObject.PHYSICAL_STATUS).keys())
    physical_status_list.insert(0, "")

    for unit in set(base_units):
        filters["measurement_unit__pk__in"] = BaseUnitValues.objects.filter(measurement_unit_base__pk=unit).values_list("measurement_unit", flat=True)
        filters["object__isnull"] = False
        shelfobjs = (
            ShelfObject.objects.filter(**filters)
            .distinct("pk")
            .values_list("object__pk", flat=True)
        )
        del filters["object__isnull"]

        for obj in set(shelfobjs):
            for physical_status in physical_status_list:
                status = ""
                physical = "physical_status" if physical_status!="" else "physical_status__isnull"
                filters[physical] = physical_status if physical=="physical_status" else True

                amount = sum([
                    get_conversion_units(shelfobj.measurement_unit, shelfobj.quantity)
                    for shelfobj in ShelfObject.objects.filter(object__pk=obj,**filters)
                    ])

                shelfobj = ShelfObject.objects.filter(object__pk=obj,**filters).first()
                del filters[physical]

                if shelfobj:
                    cas_id = shelfobj.object.cas_code
                    if shelfobj.physical_status:
                        status = shelfobj.get_physical_status_display()

                    data_column = {
                            "substance_name": shelfobj.object.name,
                            "cas_id": cas_id,
                            "quantity": amount,
                            "measurement_unit": Catalog.objects.get(pk=unit).description,
                            "physical_status": status,
                            "storage_class": shelfobj.object.get_storage_class,
                        }
                    obj_item = list(data_column.values())

                    if column_list:
                        obj_item = load_dataset_by_column(column_list, data_column)
                    if len(obj_item) > 0:
                        dataset.append(obj_item)
    return dataset

def report_reactive_stock_html(report):
    columns_fields = [
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
