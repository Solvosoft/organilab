# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-08 17:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Furniture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('type', models.CharField(choices=[('F', 'Furniture'), ('D', 'Drawer')], max_length=2, verbose_name='Type')),
            ],
            options={
                'verbose_name': 'Piece of furniture',
                'verbose_name_plural': 'Furniture',
            },
        ),
        migrations.CreateModel(
            name='LaboratoryRoom',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'Laboratory Room',
                'verbose_name_plural': 'Laboratory Rooms',
            },
        ),
        migrations.CreateModel(
            name='Object',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('0', 'Reactive'), ('1', 'Material'), ('2', 'Equipment')], max_length=2, verbose_name='Type')),
                ('code', models.CharField(max_length=255, verbose_name='Code')),
                ('description', models.TextField(verbose_name='Description')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'Object',
                'verbose_name_plural': 'Objects',
            },
        ),
        migrations.CreateModel(
            name='ObjectFeatures',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('0', 'General use'), ('1', 'Security equipment'), ('2', 'Analytic Chemistry'), ('3', 'Organic Chemistry'), ('4', 'Physical Chemistry'), ('5', 'Chemical and Biological process'), ('6', 'Industrial Biotechnology'), ('7', 'Biochemistry'), ('8', 'Water Chemistry'), ('9', 'Other')], max_length=2, verbose_name='Name')),
                ('description', models.TextField(verbose_name='Description')),
            ],
            options={
                'verbose_name': 'Object feature',
                'verbose_name_plural': 'Object features',
            },
        ),
        migrations.CreateModel(
            name='Shelf',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('C', 'Crate'), ('D', 'Drawer')], max_length=2, verbose_name='Type')),
                ('container_shelf', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='laboratory.Shelf')),
                ('furniture', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='laboratory.Furniture')),
            ],
            options={
                'verbose_name': 'Shelf',
                'verbose_name_plural': 'Shelves',
            },
        ),
        migrations.CreateModel(
            name='ShelfObject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.FloatField(verbose_name='Material quantity')),
                ('measurement_unit', models.CharField(choices=[('0', 'Meters'), ('1', 'Milimeters'), ('2', 'Centimeters'), ('3', 'Liters'), ('4', 'Mililiters')], max_length=2, verbose_name='Measurement unit')),
                ('object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='laboratory.Object')),
            ],
            options={
                'verbose_name': 'Shelf object',
                'verbose_name_plural': 'Shelf objects',
            },
        ),
        migrations.AddField(
            model_name='object',
            name='feature',
            field=models.ManyToManyField(to='laboratory.ObjectFeatures'),
        ),
        migrations.AddField(
            model_name='object',
            name='shelf',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='laboratory.Shelf'),
        ),
        migrations.AddField(
            model_name='furniture',
            name='labroom',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='laboratory.LaboratoryRoom'),
        ),
    ]