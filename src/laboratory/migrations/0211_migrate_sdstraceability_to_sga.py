# Generated manually for data migration
from django.db import migrations


def migrate_sds_to_sga(apps, schema_editor):
    """
    Link SDSTraceability records to sga.SubstanceCharacteristics
    via the object_related relationship.
    """
    SDSTraceability = apps.get_model('laboratory', 'SDSTraceability')
    SGASubstance = apps.get_model('sga', 'SubstanceCharacteristics')

    migrated = 0
    not_found = 0

    for sds in SDSTraceability.objects.filter(sustance_characteristics__isnull=False):
        # Get the Object linked to the old SustanceCharacteristics
        old_char = sds.sustance_characteristics
        if old_char and old_char.obj_id:
            # Find the corresponding SGA record via object_related
            sga_char = SGASubstance.objects.filter(
                object_related_id=old_char.obj_id
            ).first()

            if sga_char:
                sds.sga_substance_characteristics = sga_char
                sds.save(update_fields=['sga_substance_characteristics'])
                migrated += 1
            else:
                not_found += 1

    print(f"\nLinked {migrated} SDSTraceability records to SGA")
    if not_found:
        print(f"Warning: {not_found} records could not find matching SGA record")


def reverse_migration(apps, schema_editor):
    """
    Clear the sga_substance_characteristics field.
    """
    SDSTraceability = apps.get_model('laboratory', 'SDSTraceability')
    updated = SDSTraceability.objects.filter(
        sga_substance_characteristics__isnull=False
    ).update(sga_substance_characteristics=None)
    print(f"\nCleared {updated} SDSTraceability links")


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0210_sdstraceability_add_sga_fk'),
    ]

    operations = [
        migrations.RunPython(
            migrate_sds_to_sga,
            reverse_code=reverse_migration,
        ),
    ]