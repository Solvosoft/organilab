from django.db import migrations, models


def copy_laboratory_to_m2m(apps, schema_editor):
    """Pasa el laboratorio único al nuevo conjunto.

    Puede no haber nada que copiar según de dónde venga la base, pero la copia
    se hace igual: una migración de datos no debe asumir en qué estado encuentra
    la instancia que la ejecuta.
    """
    db_alias = schema_editor.connection.alias
    Substance = apps.get_model("sga", "Substance")

    through = Substance.laboratories.through
    links = [
        through(substance_id=pk, laboratory_id=laboratory_id)
        for pk, laboratory_id in Substance.objects.using(db_alias)
        .exclude(laboratory=None)
        .values_list("pk", "laboratory_id")
    ]
    if links:
        through.objects.using(db_alias).bulk_create(links, batch_size=500)
        print(f"\nCopied {len(links)} substance laboratories to the new relation")


def restore_single_laboratory(apps, schema_editor):
    """Al revertir, devuelve al FK el primer laboratorio del conjunto.

    El FK solo admite uno, así que la vuelta es necesariamente con pérdida: se
    conserva el de menor pk y los demás se descartan.
    """
    db_alias = schema_editor.connection.alias
    Substance = apps.get_model("sga", "Substance")

    through = Substance.laboratories.through
    first_by_substance = {}
    for substance_id, laboratory_id in (
        through.objects.using(db_alias)
        .order_by("pk")
        .values_list("substance_id", "laboratory_id")
    ):
        first_by_substance.setdefault(substance_id, laboratory_id)

    for substance_id, laboratory_id in first_by_substance.items():
        Substance.objects.using(db_alias).filter(pk=substance_id).update(
            laboratory_id=laboratory_id
        )


class Migration(migrations.Migration):
    """`Substance.laboratory` pasa de uno a varios."""

    dependencies = [
        ("laboratory", "0215_move_sdstraceability_to_sga"),
        ("sga", "0092_sdstraceability"),
    ]

    operations = [
        migrations.AddField(
            model_name="substance",
            name="laboratories",
            field=models.ManyToManyField(
                blank=True,
                related_name="substances_lab",
                to="laboratory.laboratory",
                verbose_name="Laboratories",
            ),
        ),
        # Va entre las dos operaciones de esquema a propósito: al revertir, el
        # RemoveField se deshace primero —recreando la columna— y esto la
        # repuebla antes de que desaparezca el M2M.
        migrations.RunPython(
            copy_laboratory_to_m2m, reverse_code=restore_single_laboratory
        ),
        migrations.RemoveField(
            model_name="substance",
            name="laboratory",
        ),
    ]
