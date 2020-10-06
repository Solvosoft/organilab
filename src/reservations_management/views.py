from django.shortcuts import render
from django.views.generic import ListView, FormView


from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from laboratory.decorators import user_group_perms

from .models import Reservations
from .forms import ReservationsForm

# Create your views here.


@method_decorator(user_group_perms(perm='laboratory.add_objectfeatures'), name='dispatch')
class ReservationsListView(LoginRequiredMixin, ListView):
    model = Reservations
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reservations'] = Reservations.objects.filter(
            laboratory__profile__user_id=self.request.user.id)
        return context


@method_decorator(user_group_perms(perm='laboratory.add_objectfeatures'), name='dispatch')
class ManageReservationView(LoginRequiredMixin, FormView):
    template_name = 'reservations_management/manage_reservation.html'
    form_class = ReservationsForm
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reservation = Reservations.objects.get(pk=self.kwargs['pk'])
        context['form'] = ReservationsForm(instance=reservation)
        return context
