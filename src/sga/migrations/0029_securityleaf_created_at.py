# Generated by Django 3.2 on 2022-10-13 16:51

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('sga', '0028_auto_20221012_1906'),
    ]

    operations = [
        migrations.AddField(
            model_name='securityleaf',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
