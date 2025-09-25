from django.core.files.base import ContentFile
from django.utils.timezone import now
from django.utils.translation import gettext as _
from laboratory.models import ShelfObject, Laboratory, BaseUnitValues, Object
from laboratory.report_utils import ExcelGraphBuilder
from laboratory.utils_base_unit import get_conversion_units
from report.utils import (
    get_report_name,
    load_dataset_by_column,
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
    filters["object__type"] = Object.MATERIAL
    containers = (
        ShelfObject.objects.filter(**filters, container__isnull=True)
        .distinct("pk")
        .values_list("object__pk", flat=True)
    )

    reactives = []
    for obj in objs:
        data_column = {}
        shelfobjects = ShelfObject.objects.filter(
            container__object__in=containers, object__pk=obj, **reactive_filters
        ).distinct("pk")
        if shelfobjects.count() > 0:
            reactive = shelfobjects.first()

            amount = sum(
                [
                    get_conversion_units(shelfobj.measurement_unit, shelfobj.quantity)
                    for shelfobj in shelfobjects
                ]
            )
            cas_id = ""
            molecular_formula = ""
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
            if hasattr(reactive.container.object, "materialcapacity"):
                capacity = reactive.container.object.materialcapacity.capacity
                capacity_measurement_unit = (
                    reactive.container.object.materialcapacity.capacity_measurement_unit.description
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
                "container": reactive.container.object.name,
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
