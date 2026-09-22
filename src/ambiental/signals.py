from django.db.models.signals import post_delete
from django.dispatch import receiver

from risk_management.models import Buildings


@receiver(post_delete, sender=Buildings, dispatch_uid="ambiental_building_access_cleanup")
def delete_building_access(sender, instance, **kwargs):
    """Al borrar un edificio se van los roles asignados sobre él."""
    from ambiental.access import building_content_type
    from auth_and_perms.models import ProfilePermission

    ProfilePermission.objects.filter(
        content_type=building_content_type(), object_id=instance.pk
    ).delete()
