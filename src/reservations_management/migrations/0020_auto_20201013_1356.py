# Generated by Django 2.2.13 on 2020-10-13 19:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations_management', '0019_reservedproducts_amount_returned'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservedproducts',
            name='amount_returned',
            field=models.FloatField(default=0),
        ),
    ]
