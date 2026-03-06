from django.contrib.admin.models import ADDITION
from django.utils.translation import gettext as _

from laboratory.logsustances import log_object_change
from laboratory.models import (
    Object,
    SustanceCharacteristics,
    MaterialCapacity,
    Catalog,
    ShelfObject,
    ShelfObjectObservation,
    ReactiveLimit,
)
from laboratory.shelfobject.utils import build_shelfobject_qr
from laboratory.utils import organilab_logentry
from laboratory.utils_base_unit import get_conversion_from_two_units


def create_reactive_limits(laboratory, object, quantity, measurement_unit):
    unit = get_units(measurement_unit).first()
    ReactiveLimit.objects.create(
        laboratory=laboratory,
        object=object,
        maximum_limit=quantity,
        minimum_limit=0,
        measurement_unit=unit,
    )


def get_units(unit):
    catalog = Catalog.objects.filter(key="units", description=unit.capitalize())
    return catalog


def validate_shelf(shelf, shelfobject_unit, quantity):
    if shelf.measurement_unit:
        return get_conversion_from_two_units(
            get_units(shelfobject_unit).first(), shelf.measurement_unit, quantity
        )
    return None


def get_reactive_by_cas_or_name(cas, name, molecular_formula, organization):
    substace_char = SustanceCharacteristics.objects.filter(
        cas_id_number=cas, molecular_formula=molecular_formula
    )
    obj = Object.objects.filter(
        type=0,
        name=name.capitalize(),
        sustancecharacteristics__in=substace_char,
        organization=organization,
    ).distinct()
    if obj.exists() and obj.count() == 1:
        print(obj)
        return obj.first()

    new_obj = Object.objects.create(
        name=name.capitalize(), type=0, organization=organization
    )
    SustanceCharacteristics.objects.create(
        obj=new_obj, cas_id_number=cas, molecular_formula=molecular_formula
    )
    return new_obj


def get_or_create_material(name, capacity, unit, organization):
    obj = Object.objects.filter(
        type=1,
        name=name.capitalize(),
        is_container=True,
        organization=organization,
    ).distinct()
    if obj.exists() and obj.count() == 1:
        return obj.first()

    container = Object.objects.create(
        name=name.capitalize(), type=1, is_container=True, organization=organization
    )
    MaterialCapacity.objects.create(
        object=container,
        capacity=capacity,
        capacity_measurement_unit=get_units(unit).first(),
    )
    return container


def create_shelfobject(data, organization_id, request):
    shelfobject = ShelfObject.objects.create(**data)
    ShelfObjectObservation.objects.create(
        shelf_object=shelfobject,
        description=_("Created"),
        action_taken=_("Object Created"),
        created_by=request.user,
    )
    organilab_logentry(
        request.user,
        shelfobject,
        ADDITION,
        "shelfobject",
        relobj=[data["in_where_laboratory"]],
    )

    log_object_change(
        request.user,
        data["in_where_laboratory"].pk,
        shelfobject,
        0,
        shelfobject.quantity,
        "",
        ADDITION,
        _("Income"),
        create=True,
        organization=organization_id,
    )
    build_shelfobject_qr(
        request, shelfobject, organization_id, shelfobject.in_where_laboratory.pk
    )
    return shelfobject
