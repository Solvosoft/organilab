from laboratory.models import ObjectLogChange


def log_object_change(user, laboratory, shelfobject, old, new, type, msg=None, create=False):
    ObjectLogChange.objects.create(
        object=shelfobject.object,
        laboratory_id=int(laboratory),
        user=user,
        old_value=old,
        new_value=new,
        diff_value=new if create else new-old,
        precursor=shelfobject.object.is_precursor,
        measurement_unit=shelfobject.measurement_unit,
        subject=msg,
        type_action=type
    )

def log_object_add_change(user, laboratory, shelfobject, old, new, msg, provider,bill, create=False):
    ObjectLogChange.objects.create(
        object=shelfobject.object,
        laboratory_id=int(laboratory),
        user=user,
        old_value=old,
        new_value=new,
        diff_value=new if create else new-old,
        precursor=shelfobject.object.is_precursor,
        measurement_unit=shelfobject.measurement_unit,
        subject=msg,
        provider_id=provider,
        bill=bill,
        type_action=1
    )
