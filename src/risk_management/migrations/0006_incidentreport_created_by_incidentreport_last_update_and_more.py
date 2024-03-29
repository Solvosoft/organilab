# Generated by Django 4.0.8 on 2022-12-20 20:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('laboratory', '0066_alter_protocol_file'),
        ('risk_management', '0005_update_sequences'),
    ]

    operations = [
        migrations.AddField(
            model_name='incidentreport',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='incidentreport',
            name='last_update',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='incidentreport',
            name='organization',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='laboratory.organizationstructure'),
        ),
        migrations.AddField(
            model_name='priorityconstrain',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='priorityconstrain',
            name='creation_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='priorityconstrain',
            name='last_update',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='priorityconstrain',
            name='organization',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='laboratory.organizationstructure'),
        ),
        migrations.AddField(
            model_name='riskzone',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='riskzone',
            name='creation_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='riskzone',
            name='last_update',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='riskzone',
            name='organization',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='laboratory.organizationstructure'),
        ),
        migrations.AddField(
            model_name='zonetype',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='zonetype',
            name='creation_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='zonetype',
            name='last_update',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='zonetype',
            name='organization',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='laboratory.organizationstructure'),
        ),
    ]
