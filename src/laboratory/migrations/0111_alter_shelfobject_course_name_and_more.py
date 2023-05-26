# Generated by Django 4.0.8 on 2023-05-25 04:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0110_shelf_infinity_quantity_alter_shelf_quantity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shelfobject',
            name='course_name',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='shelfobject',
            name='marked_as_discard',
            field=models.BooleanField(default=False, verbose_name='Is discard'),
        ),
    ]