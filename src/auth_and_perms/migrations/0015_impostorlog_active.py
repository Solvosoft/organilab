# Generated by Django 4.1.10 on 2024-05-11 23:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_and_perms', '0014_impostorwidget'),
    ]

    operations = [
        migrations.AddField(
            model_name='impostorlog',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]