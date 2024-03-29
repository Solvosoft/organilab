# Generated by Django 2.2.13 on 2020-10-12 15:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations_management', '0015_selectedproducts_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='selectedproducts',
            name='status',
            field=models.SmallIntegerField(choices=[(0, 'Requested'), (1, 'Borrowed'), (2, 'Denied'), (3, 'Selected'), (4, 'Returned')], default=3),
        ),
        migrations.AlterField(
            model_name='reservedproducts',
            name='status',
            field=models.SmallIntegerField(choices=[(0, 'Requested'), (1, 'Borrowed'), (2, 'Denied'), (3, 'Selected'), (4, 'Returned')], default=0),
        ),
    ]
