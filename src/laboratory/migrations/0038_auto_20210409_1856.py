# Generated by Django 2.2.13 on 2021-04-10 00:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0037_precursorreport'),
    ]

    operations = [
        migrations.AlterField(
            model_name='precursorreport',
            name='month',
            field=models.IntegerField(choices=[(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'), (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')]),
        ),
    ]
