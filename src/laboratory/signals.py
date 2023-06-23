from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save

from auth_and_perms.models import Profile
from laboratory.models import ShelfObject, OrganizationStructure, BaseUnitValues
from django.conf import settings
from async_notifications.utils import send_email_from_template
from laboratory.models import BlockedListNotification
from django.contrib.sites.models import Site
from decimal import Decimal


@receiver(post_save, sender=ShelfObject)
def notify_shelf_object_reach_limit(sender, **kwargs):
    instance = kwargs.get('instance')

    if instance.quantity < instance.limit_quantity:
        # send email notification
        send_email_to_ptech_limitobjs(instance)


@receiver(pre_save, sender=ShelfObject)
def shelf_object_base_quantity(sender, **kwargs):
    instance = kwargs.get('instance')
    base_unit = BaseUnitValues.objects.get(measurement_unit=instance.measurement_unit)
    if base_unit:
        quantity = Decimal(str(instance.quantity))
        base_unit_value = Decimal(str(base_unit.si_value))
        result = float(quantity / base_unit_value)
        instance.quantity_base_unit = result


@receiver(pre_save, sender=OrganizationStructure)
def add_level_organization_structure(sender, **kwargs):
    instance = kwargs.get('instance')
    if instance.parent is not None:
        instance.level = instance.parent.level + 1


def send_email_to_ptech_limitobjs(shelf_object, enqueued=True):
    labroom = shelf_object.shelf.furniture.labroom
    laboratory = labroom.laboratory
    context = {
        'shelf_object': [shelf_object],
        'labroom': labroom,
        'laboratory': laboratory
    }
    blocked = BlockedListNotification.objects.filter(
        laboratory=laboratory, object=shelf_object.object)
    blocked_emails = [x for x in blocked.values_list('user__email', flat=True)]
    ptech = Profile.objects.filter(laboratories__in=[laboratory])
    emails = [x for x in ptech.values_list('user__email', flat=True)]
    allowed_emails = [x for x in emails if x not in blocked_emails]

    for email in allowed_emails:
        schema = 'https'
        if settings.DEBUG:
            schema = 'http'
        url = f"/lab/{laboratory.pk}/blocknotifications/{shelf_object.object.pk}"
        domain = Site.objects.get_current().domain
        context['blockurl'] = f"{schema}://{domain}{url}"
        context['domain'] = domain
        send_email_from_template("Shelf object in limit",
                                 email,
                                 context=context,
                                 enqueued=enqueued,
                                 user=None,
                                 upfile=None)
