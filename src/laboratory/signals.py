from django.dispatch import receiver
from django.db.models.signals import post_save

from laboratory.models import ShelfObject, PrincipalTechnician
from django.conf import settings
from async_notifications.utils import send_email_from_template


@receiver(post_save, sender=ShelfObject)
def notify_shelf_object_reach_limit(sender, **kwargs):
    instance = kwargs.get('instance')

    if instance.quantity < instance.limit_quantity:
        # send email notification
        send_email_to_ptech_limitobjs(instance)


def send_email_to_ptech_limitobjs(shelf_object, enqueued=True):
    labroom = shelf_object.shelf.furniture.labroom
    laboratory = labroom.laboratory_set.first()
    context = {
        'shelf_object': shelf_object,
        'labroom': labroom,
        'laboratory': laboratory
    }
    ptech = PrincipalTechnician.objects.filter(assigned=laboratory)
    emails = [x['email'] for x in ptech.values('email')]
    if not emails:
        emails = [settings.DEFAULT_FROM_EMAIL]
    send_email_from_template("Shelf object in limit",
                             emails,
                             context=context,
                             enqueued=enqueued,
                             user=None,
                             upfile=None)
