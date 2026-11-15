"""Registrar la actividad resuelve su alerta (evidencia, ISO/IEC 17025 6.4.13)."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from laboratory.models import ShelfObjectCalibrate, ShelfObjectMaintenance, ShelfObjectVerification


@receiver(post_save, sender=ShelfObjectCalibrate)
@receiver(post_save, sender=ShelfObjectVerification)
@receiver(post_save, sender=ShelfObjectMaintenance)
def activity_registered(sender, instance, **kwargs):
    from laboratory.equipment.alerts import resolve_activity_alerts

    resolve_activity_alerts(instance, user=instance.created_by)
