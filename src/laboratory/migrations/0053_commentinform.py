# Generated by Django 4.0.8 on 2022-11-01 23:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('laboratory', '0052_alter_inform_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentInform',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_at', models.DateTimeField(auto_now_add=True)),
                ('comment', models.TextField(blank=True, verbose_name='Comment')),
                ('creator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Creator')),
            ],
        ),
    ]
