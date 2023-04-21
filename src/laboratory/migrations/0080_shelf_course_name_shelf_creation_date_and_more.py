# Generated by Django 4.0.8 on 2023-02-15 19:56

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0079_remove_furniture_discard_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='shelf',
            name='course_name',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='Course name'),
        ),
        migrations.AddField(
            model_name='shelf',
            name='creation_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='shelf',
            name='description',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AddField(
            model_name='shelf',
            name='laboratory_name',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='Laboratory name'),
        ),
        migrations.AddField(
            model_name='shelf',
            name='last_update',
            field=models.DateTimeField(auto_now=True),
        ),
    ]