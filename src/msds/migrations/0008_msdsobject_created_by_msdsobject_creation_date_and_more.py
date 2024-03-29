# Generated by Django 4.0.8 on 2022-12-20 17:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0066_alter_protocol_file'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('msds', '0007_msdsobject_organization'),
    ]

    operations = [
        migrations.AddField(
            model_name='msdsobject',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='msdsobject',
            name='creation_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='msdsobject',
            name='last_update',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='msdsobject',
            name='organization',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='laboratory.organizationstructure'),
        ),
    ]
