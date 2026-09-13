import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Devuelve la relación a obligatoria, como lo era antes de la migración a SGA.

    La 0210 la creó opcional solo para poder poblarla en dos pasos; una vez que la
    0211 ha vinculado todas las trazas, mantenerla opcional permitiría crear
    trazabilidad huérfana, que es justo lo contrario de lo que este modelo persigue.
    """

    dependencies = [
        ("laboratory", "0212_remove_sdstraceability_old_fk"),
        ("sga", "0089_substancecharacteristics_img_representation"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sdstraceability",
            name="sga_substance_characteristics",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="sds_traceability",
                to="sga.substancecharacteristics",
            ),
        ),
    ]
