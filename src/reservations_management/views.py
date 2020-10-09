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
    # Retrieves all accepted reserved products that are the same than the requested shelf_object product
    related_reserved_products_list = ReservedProducts.objects.filter(
        status=1, shelf_object__object=requested_product.shelf_object.object, shelf_object__shelf__furniture__labroom__laboratory__id=requested_product.reservation.laboratory.id)

    reserved_shelf_products_ids = get_shelf_products_id(
        related_reserved_products_list)

    # Retrieves shelf objects of the same laboratory with the same requested product excluding the reserved products and the requested product
    related_available_shelf_objects = ShelfObject.objects.filter(shelf__furniture__labroom__laboratory__id=requested_product.reservation.laboratory.id,
                                                                 object=requested_product.shelf_object.object).exclude(id__in=reserved_shelf_products_ids).exclude(id=requested_product.shelf_object.id)

    return {
        'related_reserved_products_list': related_reserved_products_list,
        'related_available_shelf_objects': related_available_shelf_objects
    }


def validate_reservation(request):
    is_valid = True
    if request.method == 'GET':

        requested_product = ReservedProducts.objects.get(pk=request.GET['id'])
        requested_initial_date = requested_product.initial_date
        requested_final_date = requested_product.final_date
        requested_amount_required = requested_product.amount_required
        requested_product_quantity = requested_product.shelf_object.quantity

        data_sets = get_related_data_sets(requested_product)

        reserved_product_quantity = 0
        quantity_per_reserved_product = []
        for reserved_product in data_sets['related_reserved_products_list']:
            reserved_initial_date = reserved_product.initial_date
            reserved_final_date = reserved_product.final_date

            # Si pido antes de una reserva existente y mi devolucion es cuando esa reserva inicia o antes => No acumulo
            # Si pido despues de que una reserva finaliza o exactamente cuando finaliza => No acumulo

            # Si pido antes de una reserva aceptada y mi devolucion es en periodo de una reserva existente => acumulo
            if((reserved_initial_date <= requested_initial_date) and ((reserved_final_date > requested_initial_date) and (reserved_final_date < requested_final_date) or (reserved_final_date >= requested_final_date))):
                reserved_product_quantity += reserved_product.amount_required
                quantity_per_reserved_product.append({'product_id': reserved_product.id,
                                                      'required_quantity': reserved_product.amount_required
                                                      })

            # Si pido mientras ya hay reserva aceptada => acumulo
            elif((reserved_initial_date > requested_initial_date) and (((reserved_final_date > requested_initial_date) and (reserved_final_date <= requested_final_date)) or (reserved_final_date > requested_final_date))):
                reserved_product_quantity += reserved_product.amount_required
                quantity_per_reserved_product.append({'product_id': reserved_product.id,
                                                      'required_quantity': reserved_product.amount_required
                                                      })

        # Si hay producto reservado => hay que verificar si el stock es suficiente
        if reserved_product_quantity > 0:
            remaining_amount = requested_product_quantity - reserved_product_quantity 
            # if()
            print('It is necessary to verify stock')

    return JsonResponse({'is_valid': is_valid})
