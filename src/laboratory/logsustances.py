from laboratory.models import ObjectLogChange


def log_object_change(user, laboratory, shelfobject, old, new, create=False):
    ObjectLogChange.objects.create(
        object=shelfobject.object,
        laboratory_id=int(laboratory),
        user=user,
        old_value=old,
        new_value=new,
        diff_value=new if create else new-old,
        precursor=shelfobject.object.is_precursor,
        measurement_unit=shelfobject.measurement_unit
    )
