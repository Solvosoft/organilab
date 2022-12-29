from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.shortcuts import redirect
from django.urls import reverse
from laboratory.views.djgeneric import ListView, UpdateView
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin

from laboratory.decorators import user_group_perms
from laboratory.models import OrganizationStructure
from laboratory.utils import organilab_logentry

from .models import Reservations, ReservedProducts
from .forms import ReservationsForm, ProductForm


# Create your views here.


@method_decorator(user_group_perms(perm='laboratory.add_objectfeatures'), name='dispatch')
class ReservationsListView(LoginRequiredMixin, ListView):
    model = Reservations
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reservation_list = list(ReservedProducts.objects.filter(
            laboratory__profile__user_id=self.request.user.id,
            organization__pk=self.org,
            reservation__isnull=False
        ).values_list('reservation__pk', flat=True))
        context['reservations'] = Reservations.objects.filter(pk__in=reservation_list, status=self.kwargs['status'])
        return context


@method_decorator(user_group_perms(perm='laboratory.add_objectfeatures'), name='dispatch')
class ManageReservationView(LoginRequiredMixin, UpdateView):
    template_name = 'reservations_management/manage_reservation.html'
    form_class = ReservationsForm
    model = Reservations

    def get_success_url(self, **kwargs):
        new_status = self.object.status
        success_url = reverse("reservations_management:reservations_list",kwargs={'status': new_status, 'org_pk':self.org})
        return success_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reservation_form'] = ReservationsForm(
            instance=Reservations.objects.get(pk=self.kwargs['pk']))
        context['product_form'] = ProductForm()
        return context

    def form_valid(self, form):
        dev = super().form_valid(form)
        reservation = form.save(commit=False)
        org = self.kwargs['org_pk']
        org = OrganizationStructure.objects.filter(pk=org).first()
        reservation.organization = org
        reservation.created_by = self.request.user
        reservation.save()
        organilab_logentry(self.request.user, self.object, CHANGE, relobj=self.object)
        return dev