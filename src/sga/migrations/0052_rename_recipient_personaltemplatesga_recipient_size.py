# Generated by Django 4.0.8 on 2023-06-06 03:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sga', '0051_personaltemplatesga_recipient'),
    ]

    operations = [
        migrations.RenameField(
            model_name='personaltemplatesga',
            old_name='recipient',
            new_name='recipient_size',
        ),
    ]
