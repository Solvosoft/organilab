from datetime import datetime
from collections import namedtuple

from django.views.generic import ListView, UpdateView
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse

from laboratory.decorators import user_group_perms
from laboratory.models import ShelfObject

from .models import Reservations, ReservedProducts
from .forms import ReservationsForm, ProductForm


# Create your views here.


@method_decorator(user_group_perms(perm='laboratory.add_objectfeatures'), name='dispatch')
class ReservationsListView(LoginRequiredMixin, ListView):
    model = Reservations
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reservations'] = Reservations.objects.filter(
            laboratory__profile__user_id=self.request.user.id
        )
        return context


@method_decorator(user_group_perms(perm='laboratory.add_objectfeatures'), name='dispatch')
class ManageReservationView(LoginRequiredMixin, UpdateView):
    template_name = 'reservations_management/manage_reservation.html'
    form_class = ReservationsForm
    model = Reservations
    success_url = '/reservations/list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reservation_form'] = ReservationsForm(
            instance=Reservations.objects.get(pk=self.kwargs['pk']))
        context['product_form'] = ProductForm()
        context['username'] = self.request.user.username
        context['lab_name'] = Reservations.objects.values(
            'laboratory__name').get(pk=self.kwargs['pk'])['laboratory__name']
        context['reservation_products'] = ReservedProducts.objects.filter(
            reservation_id=self.kwargs['pk'])
        return context


############## METHODS TO USE WITH AJAX ##############

def get_product_name(request):
    product_name = ''
    if request.method == 'GET':
        product_id = request.GET['id']
        product_info = ReservedProducts.objects.values(
            'shelf_object__object__name').get(id=product_id)
        product_name = product_info['shelf_object__object__name']
    return JsonResponse({'product_name': product_name})


def get_shelf_products_id(list):
    id_list = []
    for product in list:
        id_list.append(product.shelf_object.id)

    return id_list


def get_related_data_sets(requested_product):
    related_reserved_products_list = []
    related_different_reserved_products_list = []
    related_available_shelf_objects = []
    reserved_shelf_products_ids = []

    try:
        # Retrieves all accepted reserved products that are the same than the requested shelf_object product
        related_reserved_products_list = ReservedProducts.objects.filter(
            status=1,
            shelf_object=requested_product.shelf_object,
            shelf_object__shelf__furniture__labroom__laboratory__id=requested_product.reservation.laboratory.id
        )

        reserved_shelf_products_ids = get_shelf_products_id(
            related_reserved_products_list
        )

    except Exception as identifier:
        pass

    try:
        # Retrieves all accepted reserved products that are different shelf objects ,but have the same requested product
        related_different_reserved_products_list = ReservedProducts.objects.filter(
            status=1,
            shelf_object__object=requested_product.shelf_object.object,
            shelf_object__shelf__furniture__labroom__laboratory__id=requested_product.reservation.laboratory.id
        ).exclude(shelf_object=requested_product.shelf_object)

        reserved_shelf_products_ids += get_shelf_products_id(
            related_different_reserved_products_list
        )

    except Exception as identifier:
        pass

    try:
        # Retrieves shelf objects of the same laboratory with the same requested product excluding the reserved products and the requested product
        related_available_shelf_objects = ShelfObject.objects.filter(
            shelf__furniture__labroom__laboratory__id=requested_product.reservation.laboratory.id,
            object=requested_product.shelf_object.object).exclude(id__in=reserved_shelf_products_ids).exclude(id=requested_product.shelf_object.id)

    except Exception as identifier:
        pass

    return {
        'related_reserved_products_list': related_reserved_products_list,
        'related_available_shelf_objects': related_available_shelf_objects,
        'related_different_reserved_products_list': related_different_reserved_products_list
    }


def verify_reserved_products_overlap(requested_product, data_set):
    Range = namedtuple('Range', ['start', 'end'])
    reserved_product_quantity = 0
    requested_initial_date = requested_product.initial_date
    requested_final_date = requested_product.final_date

    # Loops through the reservations of the same product to verify if the request is in period of one existing reservation
    for reserved_product in data_set:
        reserved_initial_date = reserved_product.initial_date
        reserved_final_date = reserved_product.final_date

        requested_datetime_range = Range(
            start=requested_initial_date,
            end=requested_final_date
        )
        reserved_datetime_range = Range(
            start=reserved_product.initial_date,
            end=reserved_product.final_date
        )
        latest_start = max(requested_datetime_range.start,
                           reserved_datetime_range.start
                           )
        earliest_end = min(requested_datetime_range.end,
                           reserved_datetime_range.end
                           )
        delta = (earliest_end - latest_start).days + 1
        overlap = max(0, delta)

        if overlap > 0:
            reserved_product_quantity += reserved_product.amount_required

        return reserved_product_quantity


def create_reserved_product(product, amount_required, status):
    return ReservedProducts(
        shelf_object=product.shelf_object,
        reservation=product.reservation,
        is_returnable=product.is_returnable,
        amount_required=amount_required,
        initial_date=product.initial_date,
        final_date=product.final_date,
        status=status
    )


def verify_reserved_shelf_objects_stock(requested_product, product_missing_amount, related_different_reserved_products_list):
    missing_amount = product_missing_amount
    is_valid = True
    products_to_request = []

    # If there is not enough stock in the shelf object and there are more reserved shelf objects, loop through those objects to see which can be usefull
    if missing_amount < 0 and related_different_reserved_products_list:

        product_quantity_to_take = 0
        remaining_product_quantity = 0
        data_set = []

        for product in related_different_reserved_products_list:
            try:
                data_set = ReservedProducts.objects.filter(
                    status=1,
                    shelf_object=product.shelf_object,
                    shelf_object__shelf__furniture__labroom__laboratory__id=product.reservation.laboratory.id
                ).exclude(pk=product.id)

            except Exception as identifier:
                pass

            reserved_product_quantity = verify_reserved_products_overlap(
                product, data_set)

            remaining_product_quantity = missing_amount + \
                (product.shelf_object.quantity -
                 (reserved_product_quantity+product.amount_required))

            if remaining_product_quantity >= 0:
                product_quantity_to_take = product.shelf_object.quantity - \
                    (remaining_product_quantity + product.amount_required)
                missing_amount += product_quantity_to_take

                new_product_to_reserve = create_reserve_product(
                    requested_product, product_quantity_to_take, 1
                )
                products_to_request.append(new_product_to_reserve)

            else:
                product_quantity_to_take = (
                    product.shelf_object.quantity - product.amount_required)
                missing_amount += product_quantity_to_take

                new_product_to_reserve = create_reserve_product(
                    requested_product, product_quantity_to_take, 1
                )
                products_to_request.append(new_product_to_reserve)

            if missing_amount == 0:
                is_valid = True
                break

            else:
                is_valid = False

    # There is no stock and there are no reserved products
    elif missing_amount < 0 and related_different_reserved_products_list <= 0:
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

            if remaining_available_product_quantity >= 0:
                available_product_quantity_to_take = available_product.quantity - \
                    remaining_available_product_quantity
                missing_amount += available_product_quantity_to_take
                new_product_to_reserve = create_reserve_product(
                    requested_product, available_product_quantity_to_take, 1
                )
                products_to_request.append(new_product_to_reserve)

            else:
                # Cuidado con este +
                available_product_quantity_to_take = available_product.quantity
                missing_amount += available_product_quantity_to_take
                new_product_to_reserve = create_reserve_product(
                    requested_product, available_product_quantity_to_take, 1
                )
                products_to_request.append(new_product_to_reserve)

            if missing_amount == 0:
                is_valid = True
                break

            else:
                is_valid = False

    # There is no stock and there are no available products
    elif missing_amount < 0 and related_available_shelf_objects:
        is_valid = False

    return missing_amount, is_valid, products_to_request


def validate_reservation(request):
    is_valid = True
    products_to_request = []
    # CANTIDAD QUE DEBO ENVIAR PARA RESERVAR DEL PRODUCTO
    available_quantity_for_current_requested_product = 0

    if request.method == 'GET':

        requested_product = ReservedProducts.objects.get(pk=request.GET['id'])
        requested_initial_date = requested_product.initial_date
        requested_final_date = requested_product.final_date
        requested_amount_required = requested_product.amount_required
        requested_product_quantity = requested_product.shelf_object.quantity

        data_sets = get_related_data_sets(requested_product)

        reserved_product_quantity = verify_reserved_products_overlap(
            requested_product,
            data_sets['related_reserved_products_list']
        )

        # Si hay producto reservado o no me alcanza con lo que hay -> hay que verificar si el stock de otros productos reservados en relacion a lo que quiero es suficiente
        if reserved_product_quantity > 0 or (requested_product_quantity - requested_amount_required) < 0:
            product_missing_amount = \
                requested_product_quantity - \
                (reserved_product_quantity + requested_amount_required)

            available_quantity = (requested_product_quantity - reserved_product_quantity) if (
                reserved_product_quantity > 0) else requested_product_quantity

            product_missing_amount, is_valid, new_products_to_request = verify_reserved_shelf_objects_stock(
                requested_product,
                product_missing_amount,
                data_sets['related_different_reserved_products_list']
            )

            # Stores the new possible products to request
            products_to_request += new_products_to_request

            # Si no me alcanzó con los productos reservados -> verifico si en los productos disponibles que no estan reservados puedo agarrar algo
            if (product_missing_amount < 0):
                product_missing_amount, is_valid, new_products_to_request = verify_available_shelf_objects_stock(
                    requested_product,
                    product_missing_amount,
                    data_sets['related_available_shelf_objects']
                )

            products_to_request += new_products_to_request

            if product_missing_amount == 0 and is_valid:
                for new_requested_product in products_to_request:
                    print(new_requested_product.status)

            else:
                products_to_request.clear()

    return JsonResponse({
        'is_valid': is_valid,
        'available_quantity': available_quantity
    })
