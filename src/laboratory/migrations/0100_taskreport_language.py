# Generated by Django 4.1.7 on 2023-04-13 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0099_remove_laboratory_rooms'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskreport',
            name='language',
            field=models.CharField(default='es', max_length=10),
        ),
    ]
