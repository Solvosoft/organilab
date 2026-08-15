from django.db import migrations


def backfill_characteristics(apps, schema_editor):
    """Crea las características que faltan para que toda Substance tenga las suyas.

    El código asumía el invariante «toda sustancia tiene características» a través
    del accesor inverso del OneToOne, pero hay sustancias sin esa fila —creadas
    antes de que el asistente la generase— y ese accesor lanza excepción en vez
    de devolver None, tumbando el listado de sustancias.
    """
    db_alias = schema_editor.connection.alias
    Substance = apps.get_model("sga", "Substance")
    SubstanceCharacteristics = apps.get_model("sga", "SubstanceCharacteristics")

    missing = Substance.objects.using(db_alias).filter(
        substancecharacteristics__isnull=True
    )
    created = [
        SubstanceCharacteristics(substance=substance)
        for substance in missing.iterator(chunk_size=500)
    ]
    if created:
        SubstanceCharacteristics.objects.using(db_alias).bulk_create(
            created, batch_size=500
        )
        print(f"\nBackfilled {len(created)} substance characteristics")


def noop(apps, schema_editor):
    """No se borran al revertir: no distinguimos las creadas aquí de las reales."""


class Migration(migrations.Migration):

    dependencies = [
        ("sga", "0089_substancecharacteristics_img_representation"),
    ]

    operations = [
        migrations.RunPython(backfill_characteristics, reverse_code=noop),
    ]
