# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-12-13 18:02
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0014_laboratory'),
    ]

    operations = [
        migrations.AddField(
            model_name='laboratory',
            name='related_labs',
            field=models.ManyToManyField(blank=True, to='laboratory.Laboratory'),
        ),
    ]
