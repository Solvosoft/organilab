# Generated by Django 3.2 on 2022-09-12 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sga', '0015_merge_0011_auto_20220901_0957_0014_auto_20220905_1326'),
    ]

    operations = [
        migrations.AlterField(
            model_name='personaltemplatesga',
            name='preview',
            field=models.TextField(help_text='B64 preview image', null=True),
        ),
    ]
