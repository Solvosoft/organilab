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
from laboratory.utils import organilab_logentry


def create_reactive_limits(laboratory, object, quantity, measurement_unit):
    unit = get_units(measurement_unit)
    ReactiveLimit.objects.create(
        laboratory=laboratory,
        object=object,
        maximum_limit=quantity,
        minimum_limit=0,
        measurement_unit=unit,
    )


def get_units(unit):
    catalog, created = Catalog.objects.get_or_create(
        key="units", description=unit.capitalize()
    )
    return catalog


def get_reactive_by_cas_or_name(cas, name, molecular_formula, organization):
    substace_char = SustanceCharacteristics.objects.filter(
        cas_id_number=cas, molecular_formula=molecular_formula
    )
    obj = Object.objects.filter(
        type=0,
        name__icontains=name,
        sustancecharacteristics__in=substace_char,
        organization=organization,
    ).distinct()
    if obj.exists() and obj.count() == 1:
        return obj.first()

    new_obj = Object.objects.create(name=name, type=0, organization=organization)
    SustanceCharacteristics.objects.create(
        obj=new_obj, cas_id_number=cas, molecular_formula=molecular_formula
    )
    return new_obj


def get_or_create_material(name, capacity, unit, organization):
    obj = Object.objects.filter(
        type=1,
        name__icontains=name.capitalize(),
        is_container=True,
        organization=organization,
    ).distinct()
    if obj.exists() and obj.count() == 1:
        return obj
    container = Object.objects.create(
        name=name.capitalize(), type=1, is_container=True, organization=organization
    )
    MaterialCapacity.objects.create(
        object=container, capacity=capacity, capacity_measurement_unit=get_units(unit)
    )
    return container


def create_shelfobject(data, user, organization_id):
    shelfobject = ShelfObject.objects.create(**data)
    ShelfObjectObservation.objects.create(
        shelfobject=shelfobject,
        description=_("Created"),
        action_taken=_("Object Created"),
        created_by=user,
    )
    organilab_logentry(user, _("Object Created"), ADDITION, "shelfobject", created=True)

    log_object_change(
        user,
        data["in_where_laboratory"],
        shelfobject,
        0,
        shelfobject.quantity,
        "",
        ADDITION,
        _("Income"),
        create=True,
        organization=organization_id,
    )
    return shelfobject
