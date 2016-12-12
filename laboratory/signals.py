from django.dispatch import receiver
from django.db.models.signals import post_save
from laboratory.models import ShelfObject

@receiver(post_save, sender=ShelfObject)
def notify_shelf_object_reach_limit(sender, **kwargs):
    instance = kwargs.get('instance')

    if instance.quantity < instance.limit_quantity:
        # send email notification
        pass