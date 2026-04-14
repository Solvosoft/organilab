import importlib
import logging

from django.conf import settings
from django.contrib.admin.models import CHANGE
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from laboratory.logsustances import log_object_change
from laboratory.models import ShelfObjectObservation
from laboratory.utils import save_object_by_action
from .models import ReservedProducts, DENIED, BORROWED

app = importlib.import_module(settings.CELERY_MODULE).app
logger = logging.getLogger("organilab")


def _decrease_box_stock(reserved_product):
    """
    Remove the reserved boxes from quantity_units by matching their code.
    Boxes whose units drop to zero or below are removed entirely.
    quantity_box is updated to reflect the new list length.
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
    affected_codes = []

    for box in reserved_product.reserved_boxes:
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
