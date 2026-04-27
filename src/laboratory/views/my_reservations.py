from .djgeneric import ListView
from reservations_management.models import ReservedProducts, DENIED, RETURNED, SELECTED
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, permission_required


@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required(
        "reservations_management.add_reservations", raise_exception=True
    ),
    name="dispatch",
)
class MyReservationView(ListView):
    model = ReservedProducts
    template_name = "laboratory/my_reservations_list.html"
    lab_pk_field = "lab_pk"

    def get_queryset(self):
        return ReservedProducts.objects.filter(
            user=self.request.user, organization__pk=self.org, laboratory__pk=self.lab
        ).order_by("-creation_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_qs = self.get_queryset()
        context["pending_products"] = base_qs.filter(status=SELECTED)
        context["history_products"] = base_qs
        return context


MyReservationView.lab_pk_field = "lab_pk"
