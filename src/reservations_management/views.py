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

# PONER TRIES


def get_related_data_sets(requested_product):
    related_reserved_products_list = []
    related_different_reserved_products_list = []
    related_available_shelf_objects = []

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

        # Retrieves all accepted reserved products that are different shelf objects ,but have the same requested product
        related_different_reserved_products_list = ReservedProducts.objects.filter(
            status=1,
            shelf_object__object=requested_product.shelf_object.object,
            shelf_object__shelf__furniture__labroom__laboratory__id=requested_product.reservation.laboratory.id
        ).exclude(shelf_object=requested_product.shelf_object)

        reserved_shelf_products_ids += get_shelf_products_id(
            related_different_reserved_products_list
        )

        # Retrieves shelf objects of the same laboratory with the same requested product excluding the reserved products and the requested product
        related_available_shelf_objects = ShelfObject.objects.filter(shelf__furniture__labroom__laboratory__id=requested_product.reservation.laboratory.id,
                                                                     object=requested_product.shelf_object.object).exclude(id__in=reserved_shelf_products_ids).exclude(id=requested_product.shelf_object.id)

    except Exception as identifier:
        pass

    return {
        'related_reserved_products_list': related_reserved_products_list,
        'related_available_shelf_objects': related_available_shelf_objects,
        'related_different_reserved_products_list': related_different_reserved_products_list
    }


def verify_reserved_products_period(requested_product, data_set):
    reserved_product_quantity = 0
    requested_initial_date = requested_product.initial_date
    requested_final_date = requested_product.final_date

    # Loops through the reservations of the same product to verify if the request is in period of one existing reservation
    for reserved_product in data_set:
        reserved_initial_date = reserved_product.initial_date
        reserved_final_date = reserved_product.final_date

        # Si pido antes de una reserva existente y mi devolucion es cuando esa reserva inicia o antes => No acumulo
        # Si pido despues de que una reserva finaliza o exactamente cuando finaliza => No acumulo

        # Si pido antes de una reserva aceptada y mi devolucion es en periodo de una reserva existente => acumulo cuanto producto se requiere en esa reserva y de donde se agarra
        if((reserved_initial_date <= requested_initial_date) and ((reserved_final_date > requested_initial_date) and (reserved_final_date < requested_final_date) or (reserved_final_date >= requested_final_date))):
            reserved_product_quantity += reserved_product.amount_required

            # Si pido mientras ya hay reserva aceptada => acumulo cuanto producto se requiere en esa reserva y de donde se agarra
        elif((reserved_initial_date > requested_initial_date) and (((reserved_final_date > requested_initial_date) and (reserved_final_date <= requested_final_date)) or (reserved_final_date > requested_final_date))):
            reserved_product_quantity += reserved_product.amount_required

        return reserved_product_quantity


def verify_requested_shelf_objects_stock(period_missing_amount, related_different_reserved_products_list):
    missing_amount = period_missing_amount
    is_valid = False
    products_to_request = []

    # If there is not enough stock in the shelf object and there are more reserved shelf objects loop through those objects to see which can be usefull
    if missing_amount < 0 and len(related_different_reserved_products_list) > 0:

        product_quantity_to_take = 0
        remaining_product_quantity = 0
        data_set = []

        for product in related_different_reserved_products_list:
            try:
                data_set = ReservedProducts.objects.filter(
                    status=1,
                    shelf_object=product.shelf_object,
                    shelf_object__shelf__furniture__labroom__laboratory__id=product.reservation.laboratory.id
                )
            except Exception as identifier:
                pass

            product_remaining_quantity = verify_reserved_products_period(
                product, data_set)
            remaining_product_quantity = missing_amount + \
                (product.shelf_object.quantity - product.amount_required)

            if remaining_product_quantity >= 0:
                product_quantity_to_take = product.shelf_object.quantity - \
                    remaining_product_quantity
                missing_amount += product_quantity_to_take
                print(product.shelf_object.id)
                print('Create the product')

            else:
                print('Create the product again')
                print(product.shelf_object.quantity)
                product_quantity_to_take += product.shelf_object.quantity
                missing_amount += product_quantity_to_take

            if missing_amount == 0:
                print('Save products')
                is_valid = True
                break

            else:
                is_valid = False

    return missing_amount, is_valid, products_to_request


def validate_reservation(request):
    is_valid = True
    products_to_request = []
    available_quantity = 0
    if request.method == 'GET':

        requested_product = ReservedProducts.objects.get(pk=request.GET['id'])
        requested_initial_date = requested_product.initial_date
        requested_final_date = requested_product.final_date
        requested_amount_required = requested_product.amount_required
        requested_product_quantity = requested_product.shelf_object.quantity

        data_sets = get_related_data_sets(requested_product)

        reserved_product_quantity = verify_reserved_products_period(
            requested_product,
            data_sets['related_reserved_products_list']
        )
        # reserved_quantity_per_product = []

        # # Loops through the reservations of the same product to verify if the request is in period of one existing reservation
        # for reserved_product in data_sets['related_reserved_products_list']:
        #     reserved_initial_date = reserved_product.initial_date
        #     reserved_final_date = reserved_product.final_date

        #     # Si pido antes de una reserva existente y mi devolucion es cuando esa reserva inicia o antes => No acumulo
        #     # Si pido despues de que una reserva finaliza o exactamente cuando finaliza => No acumulo

        #     # Si pido antes de una reserva aceptada y mi devolucion es en periodo de una reserva existente => acumulo cuanto producto se requiere en esa reserva y de donde se agarra
        #     if((reserved_initial_date <= requested_initial_date) and ((reserved_final_date > requested_initial_date) and (reserved_final_date < requested_final_date) or (reserved_final_date >= requested_final_date))):
        #         reserved_product_quantity += reserved_product.amount_required
        #         reserved_quantity_per_product.append({
        #             'id': reserved_product.id,
        #             'required_quantity': reserved_product.amount_required,
        #             'product_quantity':  reserved_product.shelf_object.quantity
        #         })

        #     # Si pido mientras ya hay reserva aceptada => acumulo cuanto producto se requiere en esa reserva y de donde se agarra
        #     elif((reserved_initial_date > requested_initial_date) and (((reserved_final_date > requested_initial_date) and (reserved_final_date <= requested_final_date)) or (reserved_final_date > requested_final_date))):
        #         reserved_product_quantity += reserved_product.amount_required
        #         reserved_quantity_per_product.append({
        #             'id': reserved_product.id,
        #             'required_quantity': reserved_product.amount_required,
        #             'product_quantity': reserved_product.shelf_object.quantity
        #         })

        # Si hay producto reservado o no me alcanza con lo que hay => hay que verificar si el stock en relacion a lo que quiero es suficiente
        if reserved_product_quantity > 0 or (requested_product_quantity - requested_amount_required) < 0:
            period_missing_amount = \
                requested_product_quantity - \
                (reserved_product_quantity + requested_amount_required)

            available_quantity = (requested_product_quantity - reserved_product_quantity) if (
                reserved_product_quantity > 0) else requested_product_quantity

            period_missing_amount, is_valid, new_products_to_request = verify_requested_shelf_objects_stock(
                period_missing_amount,
                data_sets['related_different_reserved_products_list']
            )

            # # If there is not enough stock in the shelf object and there are more reserved shelf objects loop through those objects to see which can be usefull
            # if period_missing_amount < 0 and len(data_sets['related_different_reserved_products_list']) > 0:
            #     available_product_quantity_to_take = 0
            #     remaining_available_product_quantity = 0
            #     remaining_quantity_to_take = 0

            #     for different_reserved_shelf_object in data_sets['related_available_shelf_objects']:
            #         remaining_available_product_quantity = \
            #             period_missing_amount + \
            #             (different_reserved_shelf_object.shelf_object.quantity -
            #              different_reserved_shelf_object.amount_required)

            #         if remaining_available_product_quantity >= 0:
            #             available_product_quantity_to_take = different_reserved_shelf_object.shelf_objects.quantity - \
            #                 remaining_available_product_quantity
            #             period_missing_amount += available_product_quantity_to_take
            #             print(different_reserved_shelf_object.shelf_objects.id)
            #             print('Create the product')

            #         else:
            #             print('Create the product again')
            #             print(different_reserved_shelf_object.shelf_objects.quantity)
            #             available_product_quantity_to_take += different_reserved_shelf_object.shelf_objects.quantity
            #             period_missing_amount += available_product_quantity_to_take

            #         if period_missing_amount == 0:
            #             print('Save products')
            #             is_valid = True
            #             break

            #         else:
            #             is_valid = False

            #######################

            # available_product_quantity_to_take = 0
            # remaining_available_product_quantity = 0
            # remaining_quantity_to_take = 0

            # for different_reserved_shelf_object in data_sets['related_different_reserved_products_list']:
            #     remaining_different_reserved_shelf_object_quantity = \
            #         period_missing_amount + \
            #         (different_reserved_shelf_object.shelf_object.quantity -
            #          different_reserved_shelf_object.amount_required)

            #     if remaining_available_product_quantity >= 0:
            #         available_product_quantity_to_take = different_reserved_shelf_object.shelf_object.quantity - \
            #             remaining_available_product_quantity
            #         period_missing_amount += available_product_quantity_to_take
            #         print(different_reserved_shelf_object.id)
            #         print('Registry the product')


########################################################

            # If there is not enough stock in the shelf object and there are available products loop through the available products to see which can be usefull
            if period_missing_amount < 0 and len(data_sets['related_available_shelf_objects']) > 0:
                available_product_quantity_to_take = 0
                remaining_available_product_quantity = 0
                remaining_quantity_to_take = 0

                for available_product in data_sets['related_available_shelf_objects']:
                    remaining_available_product_quantity = \
                        period_missing_amount + available_product.quantity

                    if remaining_available_product_quantity >= 0:
                        available_product_quantity_to_take = available_product.quantity - \
                            remaining_available_product_quantity
                        period_missing_amount += available_product_quantity_to_take
                        print(available_product.id)
                        print('Create the product')

                    else:
                        print('Create the product again')
                        print(available_product.quantity)
                        available_product_quantity_to_take += available_product.quantity
                        period_missing_amount += available_product_quantity_to_take

                    if period_missing_amount == 0:
                        print('Save products')
                        is_valid = True
                        break

                    else:
                        is_valid = False

            # There is no stock and there are no available products
            elif period_missing_amount < 0 and len(data_sets['related_available_shelf_objects']) <= 0:
                is_valid = False

    return JsonResponse({'is_valid': is_valid})
