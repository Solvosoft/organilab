# Generated by Django 4.0.8 on 2023-03-09 22:19

from django.db import migrations
import zoneinfo


def createShedule(apps, schema_editor):
    CrontabSchedule = apps.get_model('django_celery_beat', 'CrontabSchedule')
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')

    schedule, _ = CrontabSchedule.objects.get_or_create(minute='23', hour='5',
                                                        day_of_week='*',
                                                        day_of_month='*',
                                                        month_of_year='*',
                                                        timezone=zoneinfo.ZoneInfo('America/Costa_Rica')
                                                        )
    PeriodicTask.objects.create(crontab=schedule,
                                name='Remove Phantoms Shelfs',
                                task='laboratory.tasks.remove_shelf_not_furniture')

class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0088_merge_20230303_2031'),
    ]

    operations = [
        migrations.RunPython(createShedule, reverse_code=migrations.RunPython.noop)
    ]
