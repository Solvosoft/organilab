# Generated by Django 4.0.8 on 2022-12-21 15:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0066_alter_protocol_file'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reservations_management', '0022_alter_reservations_comments_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservations',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='reservations',
            name='creation_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='reservations',
            name='last_update',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='reservations',
            name='organization',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='laboratory.organizationstructure'),
        ),
        migrations.AddField(
            model_name='reservedproducts',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='reservedproducts',
            name='creation_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='reservedproducts',
            name='last_update',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='reservedproducts',
            name='organization',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='laboratory.organizationstructure'),
        ),
        migrations.AlterField(
            model_name='reservations',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservation_user', to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
        migrations.AlterField(
            model_name='reservedproducts',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reserved_user', to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
    ]
