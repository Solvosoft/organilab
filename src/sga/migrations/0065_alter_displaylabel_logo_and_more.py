# Generated by Django 4.1.11 on 2023-10-17 17:18

from django.db import migrations, models
import laboratory.models_utils


class Migration(migrations.Migration):

    dependencies = [
        ('sga', '0064_rename_creator_substanceobservation_created_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='displaylabel',
            name='logo',
            field=models.FileField(blank=True, null=True, upload_to=laboratory.models_utils.upload_files, verbose_name='Logo'),
        ),
        migrations.AlterField(
            model_name='substancecharacteristics',
            name='security_sheet',
            field=models.FileField(blank=True, null=True, upload_to=laboratory.models_utils.upload_files, verbose_name='Security sheet'),
        ),
    ]