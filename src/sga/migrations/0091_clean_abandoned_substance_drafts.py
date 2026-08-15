from django.db import migrations


def clean_abandoned_drafts(apps, schema_editor):
    """Elimina las sustancias vacías que quedaron sin llegar a usarse.

    El filtro es deliberadamente estricto —sin nombre comercial, en estado
    borrador y **sin ninguna revisión asociada**— porque el criterio para borrar
    no es «parece incompleta» sino «nadie llegó a trabajar con ella». Una
    sustancia enviada a revisión, aunque esté a medias, es trabajo de alguien.
    """
    db_alias = schema_editor.connection.alias
    Substance = apps.get_model("sga", "Substance")

    abandoned = Substance.objects.using(db_alias).filter(
        comercial_name__in=["", None],
        status=0,  # Substance.DRAFT
        reviewsubstance__isnull=True,
    )
    pks = list(abandoned.values_list("pk", flat=True))
    if not pks:
        return

    deleted, detail = Substance.objects.using(db_alias).filter(pk__in=pks).delete()
    print(
        f"\nDeleted {len(pks)} abandoned substance drafts "
        f"({deleted} rows including related): {detail}"
    )


def noop(apps, schema_editor):
    """Irreversible por naturaleza: son filas vacías, no hay nada que restaurar."""


class Migration(migrations.Migration):

    dependencies = [
        ("sga", "0090_backfill_substance_characteristics"),
    ]

    operations = [
        migrations.RunPython(clean_abandoned_drafts, reverse_code=noop),
    ]
