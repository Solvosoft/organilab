from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save

from auth_and_perms.models import Profile
from laboratory.models import (
    ShelfObject,
    OrganizationStructure,
    ShelfObjectEquipmentCharacteristics,
    ShelfObjectObservation,
    Object,
)
from django.utils.translation import gettext as _
from django.conf import settings
from djgentelella.async_notification.sending import send_email_from_template
from laboratory.models import BlockedListNotification
from django.contrib.sites.models import Site
from decimal import Decimal
from laboratory.utils_base_unit import get_conversion_units

from laboratory.shelfobject_codes import assign_lot_code


@receiver(post_save, sender=ShelfObject)
def notify_shelf_object_reach_limit(sender, **kwargs):
    instance = kwargs.get("instance")

    if instance.quantity < instance.limit_quantity:
        # send email notification
        send_email_to_ptech_limitobjs(instance)


@receiver(post_save, sender=ShelfObject)
def assign_shelfobject_code(sender, **kwargs):
    """Completa el código de la etiqueta con el lote del envase.

    Va en una señal y no en las vistas porque los ShelfObject nacen por al menos
    cuatro caminos distintos (la API, los traslados, las cargas masivas) y no hay
    un punto único por el que pasen todos.
    """
    if not kwargs.get("created"):
        return
    instance = kwargs.get("instance")
    # Lo escrito a mano manda: el formulario permite teclear el código.
    if instance.shelfobject_code:
        return
    assign_lot_code(instance)


@receiver(pre_save, sender=ShelfObject)
def shelf_object_base_quantity(sender, **kwargs):
    instance = kwargs.get("instance")
    if hasattr(instance, "measurement_unit") and hasattr(instance, "quantity"):
        # Se recalcula en cada guardado: el usuario registra la cantidad en
        # cualquier unidad compatible y aquí queda expresada en la unidad base
        # de esa unidad (500 mL -> 0.5 L). Antes sólo se convertía si el campo
        # venía en None, pero su default es 0, así que casi siempre se copiaba
        # la cantidad cruda y los reportes y gráficos sumaban unidades mezcladas.
        converted = get_conversion_units(instance.measurement_unit, instance.quantity)
        # Una unidad sin BaseUnitValues no tiene unidad base conocida: se guarda
        # la cantidad tal cual porque el campo no admite nulos.
        instance.quantity_base_unit = (
            converted if converted is not None else instance.quantity
        )


def shelf_location(shelf):
    if shelf is None:
        return ""
    return " / ".join(
        str(part) for part in (shelf.furniture.labroom.laboratory, shelf.furniture.labroom, shelf.furniture, shelf)
    )


@receiver(pre_save, sender=ShelfObject)
def equipment_shelf_change(sender, instance, **kwargs):
    """Historial de ubicación del equipo (ISO/IEC 17025 6.4.13): cambio de estante."""
    if instance.pk is None or instance.object_id is None:
        return
    previous = ShelfObject.objects.filter(pk=instance.pk).select_related("object", "shelf").first()
    if previous is None or previous.shelf_id == instance.shelf_id:
        return
    if previous.object.type != Object.EQUIPMENT:
        return
    ShelfObjectObservation.objects.create(
        action_taken=_("Location change"),
        description="%s → %s" % (shelf_location(previous.shelf), shelf_location(instance.shelf)),
        shelf_object=instance,
    )


@receiver(pre_save, sender=ShelfObjectEquipmentCharacteristics)
def equipment_physical_location_change(sender, instance, **kwargs):
    """Historial de ubicación del equipo: cambio de la ubicación física específica."""
    if instance.pk is None:
        return
    previous = (
        ShelfObjectEquipmentCharacteristics.objects.filter(pk=instance.pk)
        .values_list("physical_location", flat=True)
        .first()
    )
    if previous is None or previous == instance.physical_location:
        return
    ShelfObjectObservation.objects.create(
        action_taken=_("Location change"),
        description="%s → %s" % (previous or "-", instance.physical_location or "-"),
        shelf_object_id=instance.shelfobject_id,
    )


@receiver(pre_save, sender=OrganizationStructure)
def add_level_organization_structure(sender, **kwargs):
    instance = kwargs.get("instance")
    if instance.parent is not None:
        instance.level = instance.parent.level + 1


def send_email_to_ptech_limitobjs(shelf_object, enqueued=True):
    labroom = shelf_object.shelf.furniture.labroom
    laboratory = labroom.laboratory
    context = {
        "shelf_object": [shelf_object],
        "labroom": labroom,
        "laboratory": laboratory,
    }
    blocked = BlockedListNotification.objects.filter(
        laboratory=laboratory, object=shelf_object.object
    )
    blocked_emails = [x for x in blocked.values_list("user__email", flat=True)]
    ptech = Profile.objects.filter(laboratories__in=[laboratory])
    emails = [x for x in ptech.values_list("user__email", flat=True)]
    allowed_emails = [x for x in emails if x not in blocked_emails]

    for email in allowed_emails:
        schema = "https"
        if settings.DEBUG:
            schema = "http"
        url = f"/lab/{laboratory.pk}/blocknotifications/{shelf_object.object.pk}"
        domain = Site.objects.get_current().domain
        context["blockurl"] = f"{schema}://{domain}{url}"
        context["domain"] = domain
        send_email_from_template(
            "shelf-object-in-limit",
            email,
            context=context,
            enqueued=enqueued,
            user=None,
            upfile=None,
        )
