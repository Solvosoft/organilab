# Generated by Django 4.1.11 on 2023-09-26 23:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0128_merge_0127_alter_shelf_name_0127_materialcapacity'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='object',
            options={'ordering': ['pk', 'name'], 'verbose_name': 'Object', 'verbose_name_plural': 'Objects'},
        ),
        migrations.AlterModelOptions(
            name='shelfobject',
            options={'ordering': ['pk', 'object__name'], 'verbose_name': 'Shelf object', 'verbose_name_plural': 'Shelf objects'},
        ),
    ]
