from django.shortcuts import render
from django.views.generic import ListView, UpdateView


from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse

from laboratory.decorators import user_group_perms

from .models import Reservations,ReservedProducts
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
        context['reservation_form'] = ReservationsForm(instance=Reservations.objects.get(pk=self.kwargs['pk']))
        context['product_form'] = ProductForm()
        context['username'] = self.request.user.username
        context['lab_name'] = Reservations.objects.values('laboratory__name').get(pk=self.kwargs['pk'])['laboratory__name']
        context['reservation_products'] = ReservedProducts.objects.filter(reservation_id =self.kwargs['pk'])
        return context


def get_product_name(request):
    product_name = ''
    if request.method == 'GET':
        product_id = request.GET['id']
        product_info = ReservedProducts.objects.values('shelf_object__object__name').get(id=product_id)
        product_name = product_info['shelf_object__object__name']
    return JsonResponse({'product_name': product_name})
