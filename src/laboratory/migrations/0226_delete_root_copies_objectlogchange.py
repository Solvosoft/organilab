from datetime import timedelta

from django.db import migrations

TWIN_FIELDS = (
    "object_id",
    "laboratory_id",
    "user_id",
    "old_value",
    "new_value",
    "diff_value",
    "measurement_unit_id",
    "type_action",
)


def find_root_copies(ObjectLogChange, OrganizationStructure):
    parents = dict(OrganizationStructure.objects.values_list("pk", "parent_id"))

    def root(pk):
        seen = set()
        while parents.get(pk) and pk not in seen:
            seen.add(pk)
            pk = parents[pk]
        return pk

    copies = set()
    originals = ObjectLogChange.objects.filter(
        organization_where_action_taken__parent__isnull=False
    ).values("pk", "update_time", "organization_where_action_taken_id", *TWIN_FIELDS)
    for log in originals.iterator():
        twin = (
            ObjectLogChange.objects.filter(
                pk__gt=log["pk"],
                pk__lte=log["pk"] + 3,
                organization_where_action_taken_id=root(log["organization_where_action_taken_id"]),
                update_time__gte=log["update_time"],
                update_time__lte=log["update_time"] + timedelta(seconds=2),
                **{field: log[field] for field in TWIN_FIELDS},
            )
            .exclude(pk__in=copies)
            .order_by("pk")
            .values_list("pk", flat=True)
            .first()
        )
        if twin:
            copies.add(twin)
    return copies


def delete_root_copies(apps, schema_editor):
    ObjectLogChange = apps.get_model("laboratory", "ObjectLogChange")
    OrganizationStructure = apps.get_model("laboratory", "OrganizationStructure")
    copies = find_root_copies(ObjectLogChange, OrganizationStructure)
    ObjectLogChange.objects.filter(pk__in=copies).delete()
    print("\n  ObjectLogChange: %d copias de la organización raíz eliminadas" % len(copies))


class Migration(migrations.Migration):

    dependencies = [
        ("laboratory", "0225_merge_20261015_1426"),
    ]

    operations = [
        migrations.RunPython(delete_root_copies, migrations.RunPython.noop),
    ]
