# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-12-12 15:39
from django.db import migrations, models
import laboratory.validators


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0008_auto_20161212_0922'),
    ]

    operations = [
        migrations.AlterField(
            model_name='object',
            name='molecular_formular',
            field=models.CharField(max_length=255, null=True, validators=[laboratory.validators.validate_molecular_formula], verbose_name='Molecular formula'),
        ),
    ]
