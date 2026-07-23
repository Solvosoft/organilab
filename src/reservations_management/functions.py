import importlib
import json
import math
from collections import namedtuple
from datetime import datetime, timedelta

import pytz
from django.conf import settings
from django.contrib.admin.models import CHANGE
from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_celery_beat.models import ClockedSchedule, PeriodicTask

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import ShelfObject, OrganizationStructure, ShelfObjectObservation
from laboratory.utils import organilab_logentry, save_object_by_action
from laboratory.logsustances import log_object_change
from .api.serializers import (
    ValidateReservedProductsSerializer,
)
from .models import ReservedProducts, ReservationTasks, BORROWED, RETURNED

app = importlib.import_module(settings.CELERY_MODULE).app


# ############# METHODS TO USE WITH AJAX ##############
def get_product_name_and_quantity(request, org_pk):
    product_name = ""
    if request.method == "GET":
        product = ReservedProducts.objects.get(id=request.GET["id"])
        shelf_object = product.shelf_object
        product_name = shelf_object.object.name

        if shelf_object.is_box:
            product_quantity = len(shelf_object.quantity_units)
            product_unit = str(_("boxes"))
            product_is_box = True
            reserved_boxes = product.reserved_boxes
        else:
            product_quantity = shelf_object.quantity
            product_unit = shelf_object.measurement_unit.description
            product_is_box = False
            reserved_boxes = []

    return JsonResponse(
        {
            "product_name": product_name,
            "product_quantity": product_quantity,
            "product_unit": product_unit,
            "product_is_box": product_is_box,
            "reserved_boxes": reserved_boxes,
        }
    )


def get_dates_overlap(start_date_1, final_date_1, start_date_2, final_date_2):
    Range = namedtuple("Range", ["start", "end"])

    requested_datetime_range = Range(start=start_date_1, end=final_date_1)
    reserved_datetime_range = Range(start=start_date_2, end=final_date_2)
    latest_start = max(requested_datetime_range.start, reserved_datetime_range.start)
    earliest_end = min(requested_datetime_range.end, reserved_datetime_range.end)
    delta = (earliest_end - latest_start).days + 1
    overlap = max(0, delta)

    return overlap


def verify_reserved_products_overlap(requested_product, data_set):
    # Range = namedtuple('Range', ['start', 'end'])
    reserved_product_quantity = 0
    requested_initial_date = requested_product.initial_date
    requested_final_date = requested_product.final_date

    # Loops through the reservations of the same product to verify if the request is in period of one existing reservation
    for reserved_product in data_set:
        reserved_initial_date = reserved_product.initial_date
        reserved_final_date = reserved_product.final_date

        overlap = get_dates_overlap(
            requested_initial_date,
            requested_final_date,
            reserved_initial_date,
            reserved_final_date,
        )

        # If exists overlap means that the product is reserved for the requested dates
        if overlap > 0:
            reserved_product_quantity += reserved_product.amount_required

    return reserved_product_quantity


def create_reserved_product(requested_product, amount_required, new_shelf_object):
    return ReservedProducts(
        user=requested_product.user,
        shelf_object=new_shelf_object,
        reservation=requested_product.reservation,
        is_returnable=requested_product.is_returnable,
        amount_required=amount_required,
        initial_date=requested_product.initial_date,
        final_date=requested_product.final_date,
        status=1,
    )


def verify_reserved_shelf_objects_stock(
    requested_product, product_missing_amount, related_different_reserved_products_list
):
    missing_amount = product_missing_amount
    is_valid = True
    products_to_request = []
    shelf_objects_to_skip = []

    # If there is not enough stock in the shelf object and there are more reserved shelf objects, loop through those objects to see which can be usefull
    if missing_amount < 0 and related_different_reserved_products_list:

        product_quantity_to_take = 0
        remaining_product_quantity = 0
        data_set = []

        for product in related_different_reserved_products_list:
            if product.shelf_object.id not in shelf_objects_to_skip:
                try:
                    data_set = ReservedProducts.objects.filter(
                        status=1,
                        shelf_object=product.shelf_object,
                        shelf_object__shelf__furniture__labroom__laboratory=product.laboratory,
                    ).exclude(pk=product.id)

                except Exception as identifier:
                    pass

                # Quantity of product that has been already reserved
                reserved_product_quantity = verify_reserved_products_overlap(
                    requested_product, data_set
                )

                current_product_overlap = get_dates_overlap(
                    requested_product.initial_date,
                    requested_product.final_date,
                    product.initial_date,
                    product.final_date,
                )

                # Indicates how much quantity of product will exist after to take the missing amount
                if current_product_overlap > 0:
                    remaining_product_quantity = (
                        0
                        if product.shelf_object.quantity == reserved_product_quantity
                        else missing_amount
                        + (
                            product.shelf_object.quantity
                            - (reserved_product_quantity + product.amount_required)
                        )
                    )

                else:
                    remaining_product_quantity = (
                        0
                        if product.shelf_object.quantity == reserved_product_quantity
                        else missing_amount
                        + (product.shelf_object.quantity - reserved_product_quantity)
                    )

                if remaining_product_quantity > 0:
                    product_quantity_to_take = abs(missing_amount)

                    missing_amount += product_quantity_to_take

                    new_product_to_reserve = create_reserved_product(
                        requested_product,
                        product_quantity_to_take,
                        product.shelf_object,
                    )
                    products_to_request.append(new_product_to_reserve)

                elif remaining_product_quantity < 0 or (
                    remaining_product_quantity == 0
                    and product.shelf_object.quantity != reserved_product_quantity
                ):
                    product_quantity_to_take = product.shelf_object.quantity - (
                        reserved_product_quantity + product.amount_required
                    )

                    missing_amount += product_quantity_to_take

                    if product_quantity_to_take != 0:
                        new_product_to_reserve = create_reserved_product(
                            requested_product,
                            product_quantity_to_take,
                            product.shelf_object,
                        )
                        products_to_request.append(new_product_to_reserve)

                    # There is no more quantity to reserve in this shelf object
                    shelf_objects_to_skip.append(product.shelf_object.id)

                elif product.shelf_object.quantity == reserved_product_quantity:
                    # There is no more quantity to reserve in this shelf object
                    shelf_objects_to_skip.append(product.shelf_object.id)

                if missing_amount == 0:
                    is_valid = True
                    break

                else:
                    is_valid = False

    # There is no stock and there are no reserved products
    elif missing_amount < 0 and not related_different_reserved_products_list:
        is_valid = False

    return missing_amount, is_valid, products_to_request


def verify_available_shelf_objects_stock(
    requested_product, product_missing_amount, related_available_shelf_objects
):
    missing_amount = product_missing_amount
    is_valid = True
    products_to_request = []

    # If there is not enough stock in the shelf object and there are available products, loop through the available products to see which can be usefull
    if missing_amount < 0 and related_available_shelf_objects:
        available_product_quantity_to_take = 0
        remaining_available_product_quantity = 0
        remaining_quantity_to_take = 0

        for available_product in related_available_shelf_objects:
            remaining_available_product_quantity = (
                missing_amount + available_product.quantity
            )

            if remaining_available_product_quantity > 0:

                available_product_quantity_to_take = abs(product_missing_amount)
                missing_amount += available_product_quantity_to_take
                new_product_to_reserve = create_reserved_product(
                    requested_product,
                    available_product_quantity_to_take,
                    available_product,
                )
                products_to_request.append(new_product_to_reserve)

            elif remaining_available_product_quantity <= 0:
                missing_amount += available_product.quantity
                new_product_to_reserve = create_reserved_product(
                    requested_product, available_product.quantity, available_product
                )
                products_to_request.append(new_product_to_reserve)

            if missing_amount == 0:
                is_valid = True
                break

            else:
                is_valid = False

    # There is no stock and there are no available products
    elif missing_amount < 0 and not related_available_shelf_objects:
        is_valid = False

    return missing_amount, is_valid, products_to_request


def get_shelf_products_id(list):
    id_list = []
    for product in list:
        id_list.append(product.shelf_object.id)

    return id_list


def get_related_data_sets(requested_product):
    reserved_shelf_products_ids = []

    # Retrieves all accepted reserved products that are the same than the requested shelf_object product

    related_reserved_products_list = ReservedProducts.objects.filter(
        status=1,
        shelf_object=requested_product.shelf_object,
        shelf_object__shelf__furniture__labroom__laboratory=requested_product.laboratory,
    )

    reserved_shelf_products_ids = get_shelf_products_id(related_reserved_products_list)

    # Retrieves all accepted reserved products that are different shelf objects ,but have the same requested product
    related_different_reserved_products_list = ReservedProducts.objects.filter(
        status=1,
        shelf_object__object=requested_product.shelf_object.object,
        shelf_object__shelf__furniture__labroom__laboratory=requested_product.laboratory,
    ).exclude(shelf_object=requested_product.shelf_object)

    reserved_shelf_products_ids += get_shelf_products_id(
        related_different_reserved_products_list
    )

    # Removes duplicated ids
    reserved_shelf_products_ids = list(set(reserved_shelf_products_ids))

    # Retrieves shelf objects of the same laboratory with the same requested product excluding the reserved products and the requested product
    related_available_shelf_objects = (
        ShelfObject.objects.filter(
            shelf__furniture__labroom__laboratory=requested_product.laboratory,
            object=requested_product.shelf_object.object,
        )
        .exclude(id__in=reserved_shelf_products_ids)
        .exclude(id=requested_product.shelf_object.id)
    )

    return {
        "related_reserved_products_list": related_reserved_products_list,
        "related_available_shelf_objects": related_available_shelf_objects,
        "related_different_reserved_products_list": related_different_reserved_products_list,
    }


@permission_required("laboratory.change_shelfobject")
def validate_reservation(request, org_pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)

    is_valid = True
    # New posible product to add in the reservation
    products_to_request = []
    # Available quantity that is used to reserved the current product
    available_quantity_for_current_requested_product = 0

    if request.method == "GET":
        serializer = ValidateReservedProductsSerializer(
            data=request.GET, context={"organization_id": org_pk}
        )

        if serializer.is_valid():

            requested_product = serializer.validated_data["id"]
            requested_final_date = requested_product.final_date

            if requested_final_date >= pytz.UTC.localize(datetime.now()):

                requested_amount_required = requested_product.amount_required
                requested_product_quantity = requested_product.shelf_object.quantity
                available_quantity_for_current_requested_product = (
                    requested_amount_required
                )

                # Data sets related with the requested product
                data_sets = get_related_data_sets(requested_product)

                # Quantity of product that has been already reserved
                reserved_product_quantity = verify_reserved_products_overlap(
                    requested_product, data_sets["related_reserved_products_list"]
                )

                # If there is reserved product or there is not enough product -> is necessary to verify if the stock of other reserved producst related to the quantity I want is enough
                if (
                    reserved_product_quantity > 0
                    or (requested_product_quantity - requested_amount_required) < 0
                ):

                    # Indicates how much quantity of product is neccesary to complete the reservation (negative number represents a lack of product)
                    product_missing_amount = requested_product_quantity - (
                        reserved_product_quantity + requested_amount_required
                    )

                    if product_missing_amount >= 0:
                        available_quantity_for_current_requested_product = (
                            requested_amount_required
                        )
                        product_missing_amount = 0

                    elif product_missing_amount < 0:
                        available_quantity_for_current_requested_product = (
                            requested_product_quantity - reserved_product_quantity
                        )

                        product_missing_amount, is_valid, new_products_to_request = (
                            verify_reserved_shelf_objects_stock(
                                requested_product,
                                product_missing_amount,
                                data_sets["related_different_reserved_products_list"],
                            )
                        )

                        # Stores the new possible products to request
                        products_to_request += new_products_to_request

                    # verifico si en los productos disponibles que no estan reservados puedo agarrar algo
                    # If there is not enough quantity in the reserved products and I have product missing -> verify if in the available products that have not been reserved there is enough quantity
                    if product_missing_amount < 0:
                        product_missing_amount, is_valid, new_products_to_request = (
                            verify_available_shelf_objects_stock(
                                requested_product,
                                product_missing_amount,
                                data_sets["related_available_shelf_objects"],
                            )
                        )

                        products_to_request += new_products_to_request

                    if product_missing_amount == 0 and is_valid:
                        for new_requested_product in products_to_request:
                            new_requested_product.save()
                            add_decrease_stock_task(new_requested_product)
                    else:
                        products_to_request.clear()
            else:
                is_valid = False
                available_quantity_for_current_requested_product = -1

    return JsonResponse(
        {
            "is_valid": is_valid,
            "available_quantity": available_quantity_for_current_requested_product,
        }
    )


@permission_required("laboratory.change_shelfobject")
def increase_stock(request, org_pk):
    was_increase = False

    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)

    if request.method == "GET":
        serializer = ValidateReservedProductsSerializer(
            data=request.GET, context={"organization_id": org_pk}
        )

        if serializer.is_valid():
            product = serializer.validated_data["id"]
            shelf_object = product.shelf_object

            if shelf_object.is_box:
                try:
                    boxes_to_return = json.loads(
                        request.GET.get("boxes_to_return", "[]")
                    )
                except (json.JSONDecodeError, ValueError):
                    return JsonResponse(
                        {"was_increase": False, "error": str(_("Invalid data."))}
                    )
                if not boxes_to_return:
                    return JsonResponse(
                        {"was_increase": False, "error": str(_("No boxes selected."))}
                    )
                was_increase = _increase_box_stock(
                    request.user, product, organization, boxes_to_return
                )
            else:
                amount_to_return = float(request.GET.get("amount_to_return", 0) or 0)
                was_increase = _increase_standard_stock(
                    request.user, product, amount_to_return
                )

    return JsonResponse({"was_increase": was_increase})


def _increase_standard_stock(user, product, amount_to_return):
    if amount_to_return < 0 or amount_to_return > product.amount_required:
        return False
    if amount_to_return > 0:
        product.shelf_object.quantity += amount_to_return
        product.shelf_object.save()
        organilab_logentry(
            user,
            product.shelf_object,
            CHANGE,
            changed_data=["quantity"],
            change_message=_("Returned %(amount)s units to stock from reservation")
            % {"amount": amount_to_return},
            relobj=product.shelf_object,
        )
    ReservedProducts.objects.filter(pk=product.pk).update(
        amount_returned=product.amount_returned + amount_to_return,
        status=RETURNED,
    )
    return True


def _increase_box_stock(user, product, organization, boxes_to_return):
    """
    Restores specified units per box back into quantity_units (one-time return).
    boxes_to_return: list of {'code': str, 'units': number}.
    Boxes with units > 0 are restored to the shelf.
    Boxes with units == 0 are treated as consumed — not restored, not kept.
    After this call the product status is always set to RETURNED.
    """
    shelf_object = product.shelf_object

    return_map = {item["code"]: item["units"] for item in boxes_to_return}

    quantity_units = {
        entry["code"]: entry["units"] for entry in shelf_object.quantity_units
    }
    affected_codes = []
    total_returned = 0.0

    for box in product.reserved_boxes:
        code = box["code"]
        reserved_units = box["units"]
        restore_units = return_map.get(code, 0)

        if restore_units > 0:
            old_units = quantity_units.get(code, 0)
            new_units = old_units + restore_units
            old_quantity = shelf_object.get_box_totals()
            new_quantity = (
                shelf_object.get_shelfobject_conversion_from_two_units(
                    shelf_object.shelf.measurement_unit, shelf_object.quantity
                )
                * new_units
                if shelf_object.shelf.measurement_unit
                else shelf_object.quantity * new_units
            )

            log_object_change(
                user,
                shelf_object.in_where_laboratory_id,
                shelf_object,
                old_quantity,
                new_quantity + old_quantity,
                str(_("Return via reservation #%(pk)d") % {"pk": product.pk}),
                2,
                str(_("Return")),
                create=False,
                organization=organization,
            )
            quantity_units[code] = new_units
            affected_codes.append(code)
            total_returned += restore_units / reserved_units

    if affected_codes:
        if shelf_object.shelf.measurement_unit:
            shelf_object.quantity_units = [
                {
                    "code": code,
                    "units": units,
                    "quantity": shelf_object.get_shelfobject_conversion_from_two_units(
                        shelf_object.shelf.measurement_unit, shelf_object.quantity
                    )
                    * units,
                }
                for code, units in quantity_units.items()
            ]
        else:
            shelf_object.quantity_units = [
                {
                    "code": code,
                    "units": units,
                    "quantity": shelf_object.quantity * units,
                }
                for code, units, quantity in quantity_units
            ]
        shelf_object.save(update_fields=["quantity_units"])

        ShelfObjectObservation.objects.create(
            action_taken=str(_("Box units returned")),
            description=str(
                _("Boxes %(codes)s returned from reservation #%(pk)d")
                % {
                    "codes": ", ".join(affected_codes),
                    "pk": product.pk,
                }
            ),
            shelf_object=shelf_object,
            created_by=user,
        )

    ReservedProducts.objects.filter(pk=product.pk).update(
        status=RETURNED,
        reserved_boxes=[],
        amount_returned=product.amount_returned + total_returned,
    )
    return True


def _allocate_boxes_if_needed(product):
    """
    Populates reserved_boxes if empty for a box product, using the same logic
    as ReservedShelfObjectSerializer._select_boxes (lab/shelfobject/serializers.py).
    Call this before scheduling the decrease_stock task.
    """
    shelf_object = product.shelf_object
    if not shelf_object.is_box or product.reserved_boxes:
        return

    quantity_units = shelf_object.quantity_units or []
    units_per_box = shelf_object.units_per_box or 1
    amount_required = product.amount_required

    full_count = int(amount_required)
    fraction = amount_required - full_count
    min_partial_units = math.ceil(fraction * units_per_box) if fraction > 0 else 0

    complete_boxes = [b for b in quantity_units if b["units"] >= units_per_box]
    partial_boxes = [b for b in quantity_units if b["units"] < units_per_box]

    selected = [
        {"code": b["code"], "units": units_per_box} for b in complete_boxes[:full_count]
    ]

    if min_partial_units > 0:
        for box in complete_boxes[full_count:] + partial_boxes:
            if box["units"] >= min_partial_units:
                selected.append({"code": box["code"], "units": min_partial_units})
                break

    if selected:
        product.reserved_boxes = selected
        product.save(update_fields=["reserved_boxes"])


def add_decrease_stock_task(reserved_product):

    try:
        task = ReservationTasks.objects.get(
            reserved_product__id=reserved_product.id, task_type="decrease"
        )
        app.control.revoke(task.celery_task, terminate=True)
        task.delete()

    except Exception as error:
        pass

    schedule_decrease_stock(reserved_product)

    # new_reserved_product_task = ReservationTasks(
    #     reserved_product=reserved_product, celery_task=task.id, task_type="decrease"
    # )
    #
    # new_reserved_product_task.save()


def schedule_decrease_stock(reserved_product):
    initial_date = reserved_product.initial_date
    if timezone.is_naive(initial_date):
        initial_date = timezone.make_aware(initial_date)
    clocked, _ = ClockedSchedule.objects.get_or_create(clocked_time=initial_date)
    PeriodicTask.objects.create(
        clocked=clocked,
        name=f"decrease_stock_{reserved_product.id}",
        task="reservations_management.tasks.decrease_stock",
        args=json.dumps([reserved_product.id]),
        one_off=True,
    )
