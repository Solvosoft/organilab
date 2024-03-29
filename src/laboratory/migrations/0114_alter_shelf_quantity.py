# Generated by Django 4.0.8 on 2023-05-30 19:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0113_fixed_limited_shelf'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shelf',
            name='quantity',
            field=models.FloatField(default=0, help_text='Limit quantity of the shelf', verbose_name='Quantity'),
        ),
    ]
