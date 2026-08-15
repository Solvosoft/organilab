# Generated manually for data migration
from django.db import migrations

BATCH_SIZE = 500

M2M_FIELDS = ("white_organ", "h_code", "ue_code", "nfpa", "storage_class")

SCALAR_FIELDS = (
    "iarc",
    "imdg",
    "bioaccumulable",
    "molecular_formula",
    "cas_id_number",
    "security_sheet",
    "is_precursor",
    "precursor_type",
    "valid_molecular_formula",
    "seveso_list",
    "img_representation",
    "density",
)


def _through_field_names(through, parent_model):
    """Nombres de las dos FK de una tabla intermedia: la del padre y la del destino."""
    parent_name = other_name = None
    for field in through._meta.get_fields():
        if not field.many_to_one:
            continue
        if field.related_model is parent_model and parent_name is None:
            parent_name = field.name
        else:
            other_name = field.name
    return parent_name, other_name


def migrate_characteristics_to_sga(apps, schema_editor):
    """
    Migrate all records from laboratory.SustanceCharacteristics
    to sga.SubstanceCharacteristics using object_related field.
    """
    db_alias = schema_editor.connection.alias
    LabSustance = apps.get_model("laboratory", "SustanceCharacteristics")
    SGASubstance = apps.get_model("sga", "SubstanceCharacteristics")

    through_info = {}
    for name in M2M_FIELDS:
        through = getattr(SGASubstance, name).through
        parent_name, other_name = _through_field_names(through, SGASubstance)
        through_info[name] = (through, parent_name, other_name)

    # Solo puede haber coincidencias si la migración se reejecuta: object_related
    # se crea vacío en sga.0088, así que en la primera pasada esto está vacío.
    existing = {
        object_related_id: pk
        for pk, object_related_id in SGASubstance.objects.using(db_alias)
        .exclude(object_related=None)
        .values_list("pk", "object_related_id")
    }

    migrated = 0
    updated = 0
    batch = []

    def flush():
        """Inserta el lote y sus relaciones M2M con el mínimo de sentencias."""
        nonlocal migrated
        if not batch:
            return
        SGASubstance.objects.using(db_alias).bulk_create(
            [new_row for new_row, _source in batch], batch_size=BATCH_SIZE
        )
        for name, (through, parent_name, other_name) in through_info.items():
            links = [
                through(
                    **{
                        "%s_id" % parent_name: new_row.pk,
                        "%s_id" % other_name: related.pk,
                    }
                )
                for new_row, source in batch
                for related in getattr(source, name).all()
            ]
            if links:
                through.objects.using(db_alias).bulk_create(
                    links, batch_size=BATCH_SIZE
                )
        migrated += len(batch)
        batch.clear()

    queryset = (
        LabSustance.objects.using(db_alias)
        .prefetch_related(*M2M_FIELDS)
        .order_by("pk")
    )

    for lab_char in queryset.iterator(chunk_size=BATCH_SIZE):
        values = {field: getattr(lab_char, field) for field in SCALAR_FIELDS}
        sga_pk = existing.get(lab_char.obj_id)

        if sga_pk is None:
            batch.append(
                (
                    SGASubstance(
                        object_related_id=lab_char.obj_id,
                        substance=None,
                        **values,
                    ),
                    lab_char,
                )
            )
            if len(batch) >= BATCH_SIZE:
                flush()
        else:
            # Camino de reejecución: actualiza en lugar de duplicar.
            sga_char = SGASubstance.objects.using(db_alias).get(pk=sga_pk)
            for field, value in values.items():
                setattr(sga_char, field, value)
            sga_char.save(using=db_alias)
            for name in M2M_FIELDS:
                getattr(sga_char, name).set(getattr(lab_char, name).all())
            updated += 1

    flush()

    # Comprobación de integridad: si falta alguna fila, aborta la transacción
    # antes de que las migraciones siguientes den por buena la migración.
    total_source = LabSustance.objects.using(db_alias).count()
    total_target = (
        SGASubstance.objects.using(db_alias).exclude(object_related=None).count()
    )
    if total_target < total_source:
        raise RuntimeError(
            "Migración incompleta: %d características de origen frente a %d "
            "migradas a SGA. Se aborta para no perder datos."
            % (total_source, total_target)
        )

    print(f"\nMigrated {migrated} records, updated {updated} existing records")


def reverse_migration(apps, schema_editor):
    """
    Remove migrated records (only those without substance linked).
    """
    db_alias = schema_editor.connection.alias
    SGASubstance = apps.get_model("sga", "SubstanceCharacteristics")
    # Only delete records that were migrated (have object_related but no substance)
    deleted, _ = (
        SGASubstance.objects.using(db_alias)
        .filter(object_related__isnull=False, substance__isnull=True)
        .delete()
    )
    print(f"\nDeleted {deleted} migrated records")


class Migration(migrations.Migration):

    dependencies = [
        ("laboratory", "0208_objectlogchange_deleted_user_info_and_more"),
        ("sga", "0089_substancecharacteristics_img_representation"),
    ]

    operations = [
        migrations.RunPython(
            migrate_characteristics_to_sga,
            reverse_code=reverse_migration,
        ),
    ]
