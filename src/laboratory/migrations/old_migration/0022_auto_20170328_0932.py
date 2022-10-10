# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-03-28 15:32
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0021_object_imdg_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='object',
            name='imdg_code',
            field=models.CharField(blank=True, choices=[('1', 'Explosives'), ('2', 'Gases'), ('3', 'Flammable liquids'), ('4', 'Flammable solids'), ('5', 'Oxidizing substances and organic peroxides'), ('6', 'Toxic and infectious substances'), ('7', 'Radioactive material'), ('8', 'Corrosive substances'), ('9', 'Miscellaneous dangerous substances and articles')], max_length=1, null=True, verbose_name='IMDG code'),
        ),
    ]
