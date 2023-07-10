# Generated by Django 4.0.8 on 2023-07-08 00:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('academic', '0014_auto_20230620_1622'),
    ]

    operations = [
        migrations.RenameField(
            model_name='commentprocedurestep',
            old_name='creator_at',
            new_name='created_by_at',
        ),
        migrations.RemoveField(
            model_name='commentprocedurestep',
            name='creator',
        ),
        migrations.AddField(
            model_name='commentprocedurestep',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
    ]