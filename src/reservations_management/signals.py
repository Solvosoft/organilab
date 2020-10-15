from django.dispatch import receiver
from django.db.models.signals import post_delete,pre_delete

from django.conf import settings
from .models import ReservationTasks,ReservedProducts
from celery import Celery

app = Celery()


@receiver(pre_delete, sender=ReservedProducts)
def delete_product_task_(sender, instance, **kwargs):
    if instance.id:
        try:
            task_to_delete = ReservationTasks.objects.get(reserved_product__id = instance.id)
            task_to_delete.delete()
        except : 
            pass

@receiver(post_delete, sender=ReservationTasks)
def revoke_celery_task(sender, instance, **kwargs):
    if instance.celery_task:
        app.control.revoke(instance.celery_task, terminate=True)
