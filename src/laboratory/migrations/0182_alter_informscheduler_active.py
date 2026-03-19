from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("laboratory", "0181_register_update_sds_task"),
    ]

    operations = [
        migrations.AlterField(
            model_name="informscheduler",
            name="active",
            field=models.BooleanField(default=True, verbose_name="Active"),
        ),
    ]
