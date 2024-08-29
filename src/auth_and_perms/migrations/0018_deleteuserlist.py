# Generated by Django 4.1.10 on 2024-05-18 19:59

import auth_and_perms.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth_and_perms', '0017_merge_20240518_1359'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeleteUserList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creation_date', models.DateTimeField(auto_now=True)),
                ('expiration_date', models.DateTimeField(default=auth_and_perms.models.user_expiration_date)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
