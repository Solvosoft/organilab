# Generated manually for data migration
from django.db import migrations


def migrate_characteristics_to_sga(apps, schema_editor):
    """
    Migrate all records from laboratory.SustanceCharacteristics
    to sga.SubstanceCharacteristics using object_related field.
    """
    LabSustance = apps.get_model('laboratory', 'SustanceCharacteristics')
    SGASubstance = apps.get_model('sga', 'SubstanceCharacteristics')

    migrated = 0
    skipped = 0

    for lab_char in LabSustance.objects.all():
        # Check if already exists via object_related
        existing = SGASubstance.objects.filter(object_related=lab_char.obj).first()

        if existing:
            # Update existing record with data from laboratory
            existing.iarc = lab_char.iarc
            existing.imdg = lab_char.imdg
            existing.bioaccumulable = lab_char.bioaccumulable
            existing.molecular_formula = lab_char.molecular_formula
            existing.cas_id_number = lab_char.cas_id_number
            existing.security_sheet = lab_char.security_sheet
            existing.is_precursor = lab_char.is_precursor
            existing.precursor_type = lab_char.precursor_type
            existing.valid_molecular_formula = lab_char.valid_molecular_formula
            existing.seveso_list = lab_char.seveso_list
            existing.img_representation = lab_char.img_representation
            existing.density = lab_char.density
            existing.save()

            # Copy M2M fields
            existing.white_organ.set(lab_char.white_organ.all())
            existing.h_code.set(lab_char.h_code.all())
            existing.ue_code.set(lab_char.ue_code.all())
            existing.nfpa.set(lab_char.nfpa.all())
            existing.storage_class.set(lab_char.storage_class.all())

            skipped += 1
        else:
            # Create new record in SGA
            sga_char = SGASubstance.objects.create(
                object_related=lab_char.obj,
                substance=None,  # No substance linked
                iarc=lab_char.iarc,
                imdg=lab_char.imdg,
                bioaccumulable=lab_char.bioaccumulable,
                molecular_formula=lab_char.molecular_formula,
                cas_id_number=lab_char.cas_id_number,
                security_sheet=lab_char.security_sheet,
                is_precursor=lab_char.is_precursor,
                precursor_type=lab_char.precursor_type,
                valid_molecular_formula=lab_char.valid_molecular_formula,
                seveso_list=lab_char.seveso_list,
                img_representation=lab_char.img_representation,
                density=lab_char.density,
            )

            # Copy M2M fields
            sga_char.white_organ.set(lab_char.white_organ.all())
            sga_char.h_code.set(lab_char.h_code.all())
            sga_char.ue_code.set(lab_char.ue_code.all())
            sga_char.nfpa.set(lab_char.nfpa.all())
            sga_char.storage_class.set(lab_char.storage_class.all())

            migrated += 1

    print(f"\nMigrated {migrated} records, updated {skipped} existing records")


def reverse_migration(apps, schema_editor):
    """
    Remove migrated records (only those without substance linked).
    """
    SGASubstance = apps.get_model('sga', 'SubstanceCharacteristics')
    # Only delete records that were migrated (have object_related but no substance)
    deleted, _ = SGASubstance.objects.filter(
        object_related__isnull=False,
        substance__isnull=True
    ).delete()
    print(f"\nDeleted {deleted} migrated records")


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0208_objectlogchange_deleted_user_info_and_more'),
        ('sga', '0089_substancecharacteristics_img_representation'),
    ]

    operations = [
        migrations.RunPython(
            migrate_characteristics_to_sga,
            reverse_code=reverse_migration,
        ),
    ]