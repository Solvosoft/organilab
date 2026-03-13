import zoneinfo

from django.db import migrations

TASK_NAME = 'Update SDS and extract substance data'


def register_task(apps, schema_editor):
    CrontabSchedule = apps.get_model('django_celery_beat', 'CrontabSchedule')
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')

    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='23',
        day_of_week='1',
        day_of_month='*',
        month_of_year='*',
        timezone=zoneinfo.ZoneInfo('America/Costa_Rica'),
    )

    PeriodicTask.objects.create(
        crontab=schedule,
        name=TASK_NAME,
        task='laboratory.tasks.update_sds_and_extract_data',
    )


def unregister_task(apps, schema_editor):
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
    PeriodicTask.objects.filter(name=TASK_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('django_celery_beat', '0016_alter_crontabschedule_timezone'),
        ('laboratory', '0180_alter_informscheduler_close_application_date_and_more'),
    ]

    operations = [
        migrations.RunPython(register_task, reverse_code=unregister_task),
    ]
