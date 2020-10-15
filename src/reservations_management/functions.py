from datetime import datetime
from collections import namedtuple
from django.http import JsonResponse

from laboratory.models import ShelfObject
from .models import Reservations, ReservedProducts, ReservationTasks
from .tasks import decrease_stock

from django.conf import settings


############## METHODS TO USE WITH AJAX ##############


def get_product_name_and_quantity(request):
    product_name = ''
    if request.method == 'GET':
        product = ReservedProducts.objects.get(id=request.GET['id'])
        product_name = product.shelf_object.object.name
        product_quantity = product.shelf_object.quantity
        product_unit = product.shelf_object.measurement_unit.description
    return JsonResponse({'product_name': product_name, 'product_quantity': product_quantity, 'product_unit': product_unit})


def get_dates_overlap(start_date_1, final_date_1, start_date_2, final_date_2):
    Range = namedtuple('Range', ['start', 'end'])

    requested_datetime_range = Range(
        start=start_date_1,
        end=final_date_1
    )
    reserved_datetime_range = Range(
        start=start_date_2,
        end=final_date_2
    )
    latest_start = max(requested_datetime_range.start,
                       reserved_datetime_range.start
                       )
    earliest_end = min(requested_datetime_range.end,
                       reserved_datetime_range.end
                       )
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
            requested_initial_date, requested_final_date, reserved_initial_date, reserved_final_date)

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
        status=1
    )


def verify_reserved_shelf_objects_stock(requested_product, product_missing_amount, related_different_reserved_products_list):
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
                        shelf_object__shelf__furniture__labroom__laboratory__id=product.reservation.laboratory.id
                    ).exclude(pk=product.id)

                except Exception as identifier:
                    pass

                # Quantity of product that has been already reserved
                reserved_product_quantity = verify_reserved_products_overlap(
                    requested_product, data_set)

                current_product_overlap = get_dates_overlap(
                    requested_product.initial_date,
                    requested_product.final_date,
                    product.initial_date,
                    product.final_date
                )

                # Indicates how much quantity of product will exist after to take the missing amount
                if (current_product_overlap > 0):
                    remaining_product_quantity = 0 if product.shelf_object.quantity == reserved_product_quantity else missing_amount + \
                        (product.shelf_object.quantity -
                         (reserved_product_quantity + product.amount_required))

                else:
                    remaining_product_quantity = 0 if product.shelf_object.quantity == reserved_product_quantity else missing_amount + \
                        (product.shelf_object.quantity - reserved_product_quantity)

                if remaining_product_quantity > 0:
                    product_quantity_to_take = abs(missing_amount)

                    missing_amount += product_quantity_to_take

                    new_product_to_reserve = create_reserved_product(
                        requested_product, product_quantity_to_take, product.shelf_object
                    )
                    products_to_request.append(new_product_to_reserve)

                elif remaining_product_quantity < 0 or \
                        (remaining_product_quantity == 0 and product.shelf_object.quantity != reserved_product_quantity):
                    product_quantity_to_take = product.shelf_object.quantity - \
                        (reserved_product_quantity + product.amount_required)

                    missing_amount += product_quantity_to_take

                    if product_quantity_to_take != 0:
                        new_product_to_reserve = create_reserved_product(
                            requested_product, product_quantity_to_take, product.shelf_object
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


def verify_available_shelf_objects_stock(requested_product, product_missing_amount, related_available_shelf_objects):
    missing_amount = product_missing_amount
    is_valid = True
    products_to_request = []

    # If there is not enough stock in the shelf object and there are available products, loop through the available products to see which can be usefull
    if missing_amount < 0 and related_available_shelf_objects:
        available_product_quantity_to_take = 0
        remaining_available_product_quantity = 0
        remaining_quantity_to_take = 0

        for available_product in related_available_shelf_objects:
            remaining_available_product_quantity = \
                missing_amount + available_product.quantity

            if remaining_available_product_quantity > 0:

                available_product_quantity_to_take = abs(
                    product_missing_amount)
                missing_amount += available_product_quantity_to_take
                new_product_to_reserve = create_reserved_product(
                    requested_product, available_product_quantity_to_take, available_product
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
        shelf_object__shelf__furniture__labroom__laboratory__id=requested_product.reservation.laboratory.id
    )

    reserved_shelf_products_ids = get_shelf_products_id(
        related_reserved_products_list
    )

    # Retrieves all accepted reserved products that are different shelf objects ,but have the same requested product
    related_different_reserved_products_list = ReservedProducts.objects.filter(
        status=1,
        shelf_object__object=requested_product.shelf_object.object,
        shelf_object__shelf__furniture__labroom__laboratory__id=requested_product.reservation.laboratory.id
    ).exclude(shelf_object=requested_product.shelf_object)

    reserved_shelf_products_ids += get_shelf_products_id(
        related_different_reserved_products_list
    )

    # Removes duplicated ids
    reserved_shelf_products_ids = list(set(reserved_shelf_products_ids))

    # Retrieves shelf objects of the same laboratory with the same requested product excluding the reserved products and the requested product
    related_available_shelf_objects = ShelfObject.objects.filter(
        shelf__furniture__labroom__laboratory__id=requested_product.reservation.laboratory.id,
        object=requested_product.shelf_object.object).exclude(id__in=reserved_shelf_products_ids).exclude(id=requested_product.shelf_object.id)

    return {
        'related_reserved_products_list': related_reserved_products_list,
        'related_available_shelf_objects': related_available_shelf_objects,
        'related_different_reserved_products_list': related_different_reserved_products_list
    }


def validate_reservation(request):
    is_valid = True
    # New posible product to add in the reservation
    products_to_request = []
    # Available quantity that is used to reserved the current product
    available_quantity_for_current_requested_product = 0

    if request.method == 'GET':
        requested_product = ReservedProducts.objects.get(pk=request.GET['id'])
        requested_initial_date = requested_product.initial_date
        requested_final_date = requested_product.final_date
        requested_amount_required = requested_product.amount_required
        requested_product_quantity = requested_product.shelf_object.quantity
        available_quantity_for_current_requested_product = requested_amount_required

        # Data sets related with the requested product
        data_sets = get_related_data_sets(requested_product)

        # Quantity of product that has been already reserved
        reserved_product_quantity = verify_reserved_products_overlap(
            requested_product,
            data_sets['related_reserved_products_list']
        )

        # If there is reserved product or there is not enough product -> is necessary to verify if the stock of other reserved producst related to the quantity I want is enough
        if reserved_product_quantity > 0 or (requested_product_quantity - requested_amount_required) < 0:

            # Indicates how much quantity of product is neccesary to complete the reservation (negative number represents a lack of product)
            product_missing_amount = \
                requested_product_quantity - \
                (reserved_product_quantity + requested_amount_required)

            if product_missing_amount >= 0:
                available_quantity_for_current_requested_product = requested_amount_required
                product_missing_amount = 0

            elif product_missing_amount < 0:
                available_quantity_for_current_requested_product = (
                    requested_product_quantity - reserved_product_quantity)

                product_missing_amount, is_valid, new_products_to_request = verify_reserved_shelf_objects_stock(
                    requested_product,
                    product_missing_amount,
                    data_sets['related_different_reserved_products_list']
                )

                # Stores the new possible products to request
                products_to_request += new_products_to_request

            # verifico si en los productos disponibles que no estan reservados puedo agarrar algo
            # If there is not enough quantity in the reserved products and I have product missing -> verify if in the available products that have not been reserved there is enough quantity
            if product_missing_amount < 0:
                product_missing_amount, is_valid, new_products_to_request = verify_available_shelf_objects_stock(
                    requested_product,
                    product_missing_amount,
                    data_sets['related_available_shelf_objects']
                )

                products_to_request += new_products_to_request

            if product_missing_amount == 0 and is_valid:
                for new_requested_product in products_to_request:
                    new_requested_product.save()
                    add_decrease_stock_task(new_requested_product)
            else:
                products_to_request.clear()

    return JsonResponse({
        'is_valid': is_valid,
        'available_quantity': available_quantity_for_current_requested_product
    })


def increase_stock(request):
    # Validate if is possible to compute the sum
    was_increase = False
    if request.method == 'GET':
        product = ReservedProducts.objects.get(id=request.GET['id'])
        amount_to_return = float(request.GET['amount_to_return'])

        if (product.amount_required >= product.amount_returned + amount_to_return) and amount_to_return > 0:
            product.shelf_object.quantity += amount_to_return
            was_increase = True
            product.shelf_object.save()

    return JsonResponse({'was_increase': was_increase})


def add_decrease_stock_task(reserved_product):

    task = decrease_stock.apply_async(
        args=(reserved_product.id, ),
        eta=reserved_product.initial_date
    )

    new_reserved_product_task = ReservationTasks(
        reserved_product=reserved_product,
        celery_task=task.id
    )

    new_reserved_product_task.save()
