import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Hace explícita la relación sustancia-laboratorio para poder darle código.

    La tabla `sga_substance_laboratories` ya existe: la creó `sga.0093` como
    intermedia automática del M2M. Así que el modelo se declara **solo en
    estado** y lo único que toca la base es la columna `code` nueva. Es el mismo
    patrón de `SeparateDatabaseAndState` que usan `laboratory.0215` y `sga.0092`.
    """

    dependencies = [
        ("laboratory", "0216_shelfobjectcodecounter_laboratory_code_and_more"),
        ("sga", "0093_substance_laboratories"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="SubstanceLaboratory",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        (
                            "laboratory",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                to="laboratory.laboratory",
                            ),
                        ),
                        (
                            "substance",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                to="sga.substance",
                            ),
                        ),
                    ],
                    options={
                        "verbose_name": "Substance laboratory",
                        "verbose_name_plural": "Substance laboratories",
                        "db_table": "sga_substance_laboratories",
                        "unique_together": {("substance", "laboratory")},
                    },
                ),
                migrations.AlterField(
                    model_name="substance",
                    name="laboratories",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="substances_lab",
                        through="sga.SubstanceLaboratory",
                        to="laboratory.laboratory",
                        verbose_name="Laboratories",
                    ),
                ),
            ],
            database_operations=[],
        ),
        # Las dos columnas que la tabla intermedia automática no tenía. Ambas
        # anulables a propósito: las filas que ya existan no las traen.
        migrations.AddField(
            model_name="substancelaboratory",
            name="code",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=50,
                null=True,
                verbose_name="Code",
            ),
        ),
        migrations.AddField(
            model_name="substancelaboratory",
            name="creation_date",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
