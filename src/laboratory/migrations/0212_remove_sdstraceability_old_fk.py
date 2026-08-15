# Generated manually for data migration
from django.db import migrations

BATCH_SIZE = 500


def noop(apps, schema_editor):
    """Hacia adelante no hay nada que hacer: la columna se elimina después."""


def restore_old_fk(apps, schema_editor):
    """
    Repuebla `sustance_characteristics` al revertir, a partir del vínculo SGA.

    Sin esto la reversa completa es imposible: la 0212 recrea la columna vacía y
    la reversa de la 0210 intenta devolverle el NOT NULL original, que falla con
    IntegrityError. Se reconstruye el vínculo por el `Object` compartido, que es
    la misma correspondencia que usó la 0211 en sentido contrario.
    """
    db_alias = schema_editor.connection.alias
    SDSTraceability = apps.get_model("laboratory", "SDSTraceability")
    LabSustance = apps.get_model("laboratory", "SustanceCharacteristics")
    SGASubstance = apps.get_model("sga", "SubstanceCharacteristics")

    lab_by_object = dict(
        LabSustance.objects.using(db_alias).values_list("obj_id", "pk")
    )
    object_by_sga = dict(
        SGASubstance.objects.using(db_alias)
        .exclude(object_related=None)
        .values_list("pk", "object_related_id")
    )

    restored = 0
    pending = []
    queryset = (
        SDSTraceability.objects.using(db_alias)
        .filter(sga_substance_characteristics__isnull=False)
        .order_by("pk")
    )

    for sds in queryset.iterator(chunk_size=BATCH_SIZE):
        object_id = object_by_sga.get(sds.sga_substance_characteristics_id)
        lab_pk = lab_by_object.get(object_id) if object_id else None
        if lab_pk is None:
            continue
        sds.sustance_characteristics_id = lab_pk
        pending.append(sds)
        restored += 1
        if len(pending) >= BATCH_SIZE:
            SDSTraceability.objects.using(db_alias).bulk_update(
                pending, ["sustance_characteristics"], batch_size=BATCH_SIZE
            )
            pending.clear()

    if pending:
        SDSTraceability.objects.using(db_alias).bulk_update(
            pending, ["sustance_characteristics"], batch_size=BATCH_SIZE
        )

    print(f"\nRestored {restored} SDSTraceability links to the legacy model")


class Migration(migrations.Migration):

    dependencies = [
        ("laboratory", "0211_migrate_sdstraceability_to_sga"),
    ]

    operations = [
        # Debe ir ANTES del RemoveField: al revertir, las operaciones se
        # deshacen en orden inverso, así que primero se recrea la columna y
        # después este RunPython la repuebla.
        migrations.RunPython(noop, reverse_code=restore_old_fk),
        migrations.RemoveField(
            model_name="sdstraceability",
            name="sustance_characteristics",
        ),
    ]
