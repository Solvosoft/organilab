# Generated by Django 4.0.8 on 2023-03-03 22:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0086_alter_registeruserqr_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shelf',
            name='description',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Description'),
        ),
    ]
