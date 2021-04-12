from __future__ import absolute_import, unicode_literals

from celery import Celery
from laboratory.models import ShelfObject, Laboratory,PrecursorReport
from laboratory.signals import send_email_to_ptech_limitobjs

from django.db.models.expressions import F
from datetime import date

app = Celery()


@app.task
def notify_about_product_limit_reach():
    limited_shelf_objects = get_limited_shelf_objects()

    for shelf_object in limited_shelf_objects:
        send_email_to_ptech_limitobjs(shelf_object, enqueued=False)


@app.on_after_configure.connect
def setup_daily_tasks(sender, **kwargs):
    sender.add_periodic_task(
        2, notify_about_product_limit_reach.s(), name='notify')


def get_limited_shelf_objects():
    return ShelfObject.objects.filter(quantity__lte=F('limit_quantity'))

@app.task()
def create_precursor_reports():
    day = date.today()
    for lab in Laboratory.objects.all():
        PrecursorReport.objects.create(
                month=day.month,
                year=day.year,
                laboratory=lab,
                consecutive=add_consecutive(lab)
            )


def add_consecutive(lab):
    report = PrecursorReport.objects.filter(laboratory=lab).last()
    consecutive = 1
    if report is not None:
        consecutive = int(report.consecutive)+1

    return consecutive