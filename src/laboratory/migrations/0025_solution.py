# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-05-08 16:42
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0024_laboratory_students'),
    ]

    operations = [
        migrations.CreateModel(
            name='Solution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('solutes', models.TextField(verbose_name='Solutes')),
                ('volume', models.CharField(max_length=100, verbose_name='Volumen')),
                ('temperature', models.IntegerField(default=25, verbose_name='Temperature')),
                ('pressure', models.IntegerField(default=1, verbose_name='Pressure')),
                ('pH', models.IntegerField(default=7, verbose_name='pH')),
            ],
            options={
                'verbose_name': 'Solution',
                'verbose_name_plural': 'Solutions',
            },
        ),
    ]
