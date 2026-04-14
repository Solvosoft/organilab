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
    attrs = dict(
        object=shelfobject.object,
        laboratory_id=int(laboratory),
        user=user,
        old_value=old,
        new_value=new,
        diff_value=new if create else new - old,
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
    attrs = dict(
        object=shelfobject.object,
        laboratory_id=int(laboratory),
        user=user,
        old_value=old,
        new_value=new,
        diff_value=new if create else new - old,
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
