from django.conf import settings
from django.contrib.admin.models import CHANGE, ADDITION
from django.shortcuts import get_object_or_404

from laboratory.models import ObjectLogChange, OrganizationStructure


def log_object_change(
    user,
    laboratory,
    shelfobject,
    old,
    new,
    note,
    type_action,
    msg=None,
    create=False,
    organization=None,
):
    factor = sum(b["units"] for b in shelfobject.quantity_units) if shelfobject.is_box and shelfobject.quantity_units else 1
    old_total = old * factor
    new_total = new * factor
    attrs = dict(
        object=shelfobject.object,
        laboratory_id=int(laboratory),
        user=user,
        old_value=old_total,
        new_value=new_total,
        diff_value=new_total if create else new_total - old_total,
        precursor=shelfobject.object.is_precursor,
        measurement_unit=shelfobject.measurement_unit,
        subject=msg,
        type_action=type_action,
        note=note,
    )
    if isinstance(organization, (int, str)):
        attrs["organization_where_action_taken_id"] = organization
    else:
        attrs["organization_where_action_taken"] = organization
    ObjectLogChange.objects.create(**attrs)


def log_object_add_change(
    user,
    laboratory,
    shelfobject,
    old,
    new,
    msg,
    provider,
    bill,
    create=False,
    organization=None,
):
    factor = sum(b["units"] for b in shelfobject.quantity_units) if shelfobject.is_box and shelfobject.quantity_units else 1
    old_total = old * factor
    new_total = new * factor
    attrs = dict(
        object=shelfobject.object,
        laboratory_id=int(laboratory),
        user=user,
        old_value=old_total,
        new_value=new_total,
        diff_value=new_total if create else new_total - old_total,
        precursor=shelfobject.object.is_precursor,
        measurement_unit=shelfobject.measurement_unit,
        subject=msg,
        type_action=ADDITION,
        provider=provider,
        bill=bill,
        note="",
    )
    if isinstance(organization, (int, str)):
        attrs["organization_where_action_taken_id"] = organization
    else:
        attrs["organization_where_action_taken"] = organization
    ObjectLogChange.objects.create(**attrs)
