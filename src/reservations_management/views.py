from django.contrib.admin.models import CHANGE
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse

from auth_and_perms.models import ProfilePermission
from laboratory.models import OrganizationStructure
from laboratory.utils import organilab_logentry, get_lab_ids
from laboratory.views.djgeneric import ListView, UpdateView
from .forms import ReservationsForm, ProductForm
from .models import Reservations, ReservedProducts


class ReservationsListView(PermissionRequiredMixin, ListView):
    model = Reservations
    paginate_by = 10
    permission_required = "laboratory.add_objectfeatures"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = OrganizationStructure.objects.filter(pk=self.kwargs["org_pk"]).first()
        user = self.request.user
        profile = getattr(user, "profile", None)
        lab_ids = get_lab_ids(org, profile)
        reservation_list = ReservedProducts.objects.filter(
            reservation__isnull=False,
            laboratory__id__in=lab_ids,
        ).values_list("reservation__pk", flat=True).distinct()

        context["reservations"] = Reservations.objects.filter(
            pk__in=reservation_list, status=self.kwargs["status"]
        )
        return context


class ManageReservationView(PermissionRequiredMixin, UpdateView):
    template_name = "reservations_management/manage_reservation.html"
    form_class = ReservationsForm
    model = Reservations
    permission_required = "laboratory.add_objectfeatures"

    def get_success_url(self, **kwargs):
        new_status = self.object.status
        success_url = reverse(
            "reservations_management:reservations_list",
            kwargs={"status": new_status, "org_pk": self.org},
        )
        return success_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reservation_form"] = ReservationsForm(
            instance=Reservations.objects.get(pk=self.kwargs["pk"])
        )
        context["product_form"] = ProductForm()
        return context

    def form_valid(self, form):
        dev = super().form_valid(form)
        reservation = form.save(commit=False)
        org = self.kwargs["org_pk"]
        org = OrganizationStructure.objects.filter(pk=org).first()
        reservation.organization = org
        reservation.created_by = self.request.user
        reservation.save()
        organilab_logentry(self.request.user, self.object, CHANGE, relobj=self.object)
        return dev
