import importlib
import logging

from django.conf import settings
from django.contrib.admin.models import CHANGE
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_celery_beat.models import PeriodicTask
from djgentelella.models import Notification
from laboratory.logsustances import log_object_change
from laboratory.models import ShelfObjectObservation
from laboratory.utils import save_object_by_action
from .models import ReservedProducts, DENIED, BORROWED

app = importlib.import_module(settings.CELERY_MODULE).app
logger = logging.getLogger("organilab")


def _find_replacement_boxes(missing_units_needed, available_units_map, excluded_codes):
    """
    Find boxes from available_units_map to cover missing_units_needed total units.
    excluded_codes are already-reserved codes that cannot be used as replacements.
    Returns (replacements, units_not_covered) where replacements is a list of
    {'code': ..., 'units': ...} entries.
    """
    replacements = []
    remaining = missing_units_needed
    for code, units in available_units_map.items():
        if remaining <= 0:
            break
        if code in excluded_codes:
            continue
        take = min(units, remaining)
        replacements.append({"code": code, "units": take})
        remaining -= take
    return replacements, remaining


def _decrease_box_stock(reserved_product):
    """
    Remove the reserved boxes from quantity_units by matching their code.
    If a reserved box no longer exists in quantity_units (deleted externally),
    replacement boxes are sourced from the available stock to cover the same
    unit total. reserved_boxes is updated to reflect the actual boxes consumed.
    Boxes whose units drop to zero or below are removed entirely.
    Audit log and observation are recorded on behalf of the reservation owner.
    """
    user = reserved_product.user
    laboratory = reserved_product.laboratory
    organization = reserved_product.organization
    shelfobject = reserved_product.shelf_object

    quantity_units = {
        entry["code"]: entry["units"]
        for entry in shelfobject.quantity_units
    }

    existing_boxes = []
    missing_boxes = []
    for box in reserved_product.reserved_boxes:
        if box["code"] in quantity_units:
            existing_boxes.append(box)
        else:
            missing_boxes.append(box)

    replacement_boxes = []
    if missing_boxes:
        missing_units_needed = sum(b["units"] for b in missing_boxes)
        excluded_codes = {b["code"] for b in existing_boxes}
        replacement_boxes, units_not_covered = _find_replacement_boxes(
            missing_units_needed, quantity_units, excluded_codes
        )
        if units_not_covered > 0:
            logger.warning(
                "Reservation #%d: not enough stock to replace %s missing boxes (%s units short), denying.",
                reserved_product.pk,
                len(missing_boxes),
                units_not_covered,
            )
            Notification.objects.create(
                state="visible",
                user=reserved_product.user,
                message_type="warning",
                description=_("Your reservation #%(pk)d was denied: not enough box stock to fulfill the request (%(units)d units short).") % {
                    "pk": reserved_product.pk,
                    "units": units_not_covered,
                },
            )
            reserved_product.status = DENIED
            reserved_product.save(update_fields=["status"])
            return

    final_reserved_boxes = existing_boxes + replacement_boxes
    if replacement_boxes:
        reserved_product.reserved_boxes = final_reserved_boxes
        reserved_product.save(update_fields=["reserved_boxes"])

    affected_codes = []
    for box in final_reserved_boxes:
        code = box["code"]
        reserved_units = box["units"]
        current_units = quantity_units.get(code, 0)
        new_units = current_units - reserved_units

        log_object_change(
            user,
            laboratory.pk,
            shelfobject,
            current_units,
            max(new_units, 0),
            _("Automatic decrease via reservation #%(pk)d") % {"pk": reserved_product.pk},
            2,
            _("Spend"),
            create=False,
            organization=organization,
        )

        if new_units <= 0:
            quantity_units.pop(code, None)
        else:
            quantity_units[code] = new_units

        affected_codes.append(code)

    shelfobject.quantity_units = [
        {"code": code, "units": units}
        for code, units in quantity_units.items()
    ]

    save_object_by_action(
        user,
        shelfobject,
        [laboratory, shelfobject, organization],
        ["quantity_units"],
        CHANGE,
        "shelfobject",
    )

    ShelfObjectObservation.objects.create(
        action_taken=_("Box units decreased via reservation"),
        description=_("Boxes %(codes)s consumed automatically from reservation #%(pk)d") % {
            "codes": ", ".join(affected_codes),
            "pk": reserved_product.pk,
        },
        shelf_object=shelfobject,
        created_by=user,
    )

    reserved_product.status = BORROWED
    reserved_product.save(update_fields=["status"])


@app.task
def decrease_stock(reserved_product):
    """
    Decrease the stock of a reserved product when its initial_date arrives.

    For box shelf objects, removes the reserved_boxes entries from quantity_units
    by code and updates quantity_box without touching quantity.
    For standard shelf objects, subtracts amount_required from quantity.
    """
    reserved_product_pk = reserved_product if not isinstance(reserved_product, ReservedProducts) else reserved_product.pk
    try:
        if not isinstance(reserved_product, ReservedProducts):
            try:
                reserved_product = ReservedProducts.objects.get(pk=reserved_product)
            except Exception as e:
                logger.error("Decrease stock", exc_info=e)
                return

        if reserved_product.final_date < timezone.now():
            reserved_product.status = DENIED
            reserved_product.save(update_fields=["status"])
            return

        if reserved_product.shelf_object.is_box:
            _decrease_box_stock(reserved_product)
            return

        quantity = reserved_product.shelf_object.quantity
        if (quantity - reserved_product.amount_required) < 0:
            reserved_product.shelf_object.quantity = 0
        else:
            reserved_product.shelf_object.quantity = (
                quantity - reserved_product.amount_required
            )
        reserved_product.shelf_object.save()
    finally:
        PeriodicTask.objects.filter(name=f"decrease_stock_{reserved_product_pk}").delete()
