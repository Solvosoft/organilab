# Generated by Django 4.1.9 on 2023-05-15 18:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0104_shelfobjectlimits_expiration_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shelf',
            name='quantity',
            field=models.FloatField(default=-1, help_text='Use dot like 0.344 on decimal', verbose_name='Quantity'),
        ),
    ]
