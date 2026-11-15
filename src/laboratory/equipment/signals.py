"""Registrar la actividad resuelve su alerta (evidencia, ISO/IEC 17025 6.4.13)."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from laboratory.models import (
    ControlPoint,
    EquipmentActivityPlan,
    ShelfObjectCalibrate,
    ShelfObjectMaintenance,
    ShelfObjectVerification,
)


@receiver(post_save, sender=ShelfObjectCalibrate)
@receiver(post_save, sender=ShelfObjectVerification)
@receiver(post_save, sender=ShelfObjectMaintenance)
def activity_registered(sender, instance, **kwargs):
    from laboratory.equipment.alerts import resolve_activity_alerts

    resolve_activity_alerts(instance, user=instance.created_by)


@receiver(post_save, sender=EquipmentActivityPlan)
@receiver(post_save, sender=ControlPoint)
def default_alert_rule(sender, instance, created, raw=False, **kwargs):
    """El primer programa o punto de control de una organización deja su regla de alerta."""
    if not created or raw:
        return
    from laboratory.equipment import alerts, control

    laboratory = instance.shelfobject.in_where_laboratory
    if laboratory is None:
        return
    process = control.PROCESS if sender is ControlPoint else alerts.PROCESS
    alerts.ensure_default_rule(process, laboratory.organization, instance.created_by)
