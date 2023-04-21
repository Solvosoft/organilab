# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-21 06:20
from __future__ import unicode_literals
from django.db import migrations, models

import django.db.models.deletion
try:
    import mptt.fields as mpttfields
except:
    mpttfields = None


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0034_group_perms'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='laboratory',
            name='related_labs',
        ),
        migrations.AlterField(
            model_name='laboratory',
            name='organization',
            field=mpttfields.TreeForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             to='laboratory.OrganizationStructure') if mpttfields else models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to='laboratory.OrganizationStructure'),
        ),
    ]