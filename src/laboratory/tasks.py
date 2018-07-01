from __future__ import absolute_import, unicode_literals

from celery import Celery
from laboratory.models import ShelfObject
from laboratory.signals import send_email_to_ptech_limitobjs

from django.db.models.expressions import F


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
