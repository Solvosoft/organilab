# Generated manually for data migration
from django.db import migrations

BATCH_SIZE = 500


def migrate_sds_to_sga(apps, schema_editor):
    """
    Link SDSTraceability records to sga.SubstanceCharacteristics
    via the object_related relationship.
    """
    db_alias = schema_editor.connection.alias
    SDSTraceability = apps.get_model("laboratory", "SDSTraceability")
    SGASubstance = apps.get_model("sga", "SubstanceCharacteristics")

    # Un único mapa obj -> característica SGA en vez de una consulta por traza.
    sga_by_object = dict(
        SGASubstance.objects.using(db_alias)
        .exclude(object_related=None)
        .values_list("object_related_id", "pk")
    )

    migrated = 0
    not_found = 0
    pending = []

    queryset = (
        SDSTraceability.objects.using(db_alias)
        .filter(sustance_characteristics__isnull=False)
        .select_related("sustance_characteristics")
        .order_by("pk")
    )

    for sds in queryset.iterator(chunk_size=BATCH_SIZE):
        old_char = sds.sustance_characteristics
        sga_pk = sga_by_object.get(old_char.obj_id) if old_char else None

        if sga_pk is None:
            not_found += 1
            continue

        sds.sga_substance_characteristics_id = sga_pk
        pending.append(sds)
        migrated += 1

        if len(pending) >= BATCH_SIZE:
            SDSTraceability.objects.using(db_alias).bulk_update(
                pending, ["sga_substance_characteristics"], batch_size=BATCH_SIZE
            )
            pending.clear()

    if pending:
        SDSTraceability.objects.using(db_alias).bulk_update(
            pending, ["sga_substance_characteristics"], batch_size=BATCH_SIZE
        )

    # La migración 0212 elimina la columna de origen, así que un vínculo sin
    # migrar aquí se perdería para siempre. Abortamos antes de llegar a eso.
    if not_found:
        raise RuntimeError(
            "%d registros de SDSTraceability no encontraron su equivalente en SGA. "
            "Se aborta la migración: la 0212 eliminaría la columna de origen y esos "
            "vínculos se perderían de forma irreversible." % not_found
        )

    print(f"\nLinked {migrated} SDSTraceability records to SGA")


def reverse_migration(apps, schema_editor):
    """
    Clear the sga_substance_characteristics field.
    """
    db_alias = schema_editor.connection.alias
    SDSTraceability = apps.get_model("laboratory", "SDSTraceability")
    updated = (
        SDSTraceability.objects.using(db_alias)
        .filter(sga_substance_characteristics__isnull=False)
        .update(sga_substance_characteristics=None)
    )
    print(f"\nCleared {updated} SDSTraceability links")


class Migration(migrations.Migration):

    dependencies = [
        ("laboratory", "0210_sdstraceability_add_sga_fk"),
    ]

    operations = [
        migrations.RunPython(
            migrate_sds_to_sga,
            reverse_code=reverse_migration,
        ),
    ]
