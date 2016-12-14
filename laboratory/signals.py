from django.dispatch import receiver
from django.db.models.signals import post_save
from django.template.loader import render_to_string

from laboratory.models import ShelfObject
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


@receiver(post_save, sender=ShelfObject)
def notify_shelf_object_reach_limit(sender, **kwargs):
    instance = kwargs.get('instance')

    get_laboratory_users()
    if instance.quantity < instance.limit_quantity:
        # send email notification
        send_notification_email(shelf_object=instance)


def get_laboratory_users():
    lab_groups = [
        'laboratory_admin',
        'laboratory_worker'
    ]
    users_emails = []

    for group in Group.objects.filter(name__in=lab_groups):
        for user in group.user_set.all():
            users_emails.append(user.email)

    return set(users_emails)


def send_notification_email(shelf_object):
    subject = 'The shelf object called %s reached its limit quantity' % shelf_object.object.name

    context = {
        'shelf_object': shelf_object
    }

    html_message = render_to_string('email/shelf_object_quantity_limit.html', context=context)

    send_mail(
        subject=subject,
        message=_('Please use an email client with HTML support'),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=get_laboratory_users(),
        fail_silently=True,
        html_message=html_message
    )
