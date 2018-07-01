from __future__ import absolute_import, unicode_literals

from celery import Celery
from django.conf import settings
from django.template.loader import render_to_string

from laboratory.models import ShelfObject
from laboratory.signals import get_laboratory_users
from django.utils.translation import ugettext_lazy as _

app = Celery()


@app.task
def notify_about_product_limit_reach():
    send_email()


@app.on_after_configure.connect
def setup_daily_tasks(sender, **kwargs):
    sender.add_periodic_task(
        2, notify_about_product_limit_reach.s(), name='notify')


def send_email():
    subject = _('Products that reached the limit quantity today')

    limited_shelf_objects = get_limited_shelf_objects()

    context = {
        'shelf_objects': limited_shelf_objects
    }

    html_message = render_to_string(
        'email/object_list_reach_quantity_limit.html', context=context)

    from django.core.mail import send_mail
    send_mail(
        subject=subject,
        message=_('Please use an email client with HTML support'),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=get_laboratory_users(),
        fail_silently=True,
        html_message=html_message
    )


def get_limited_shelf_objects():
    for shelf_object in ShelfObject.objects.all():
        if shelf_object.limit_reached:
            yield shelf_object
