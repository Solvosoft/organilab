# Generated by Django 4.1.8 on 2023-06-16 16:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('laboratory', '0114_alter_shelf_quantity'),
        ('sga', '0060_reviewsubstance_created_by_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='PersonalTemplateSGA',
            new_name='DisplayLabel',
        ),

    ]
