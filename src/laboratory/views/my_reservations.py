from .djgeneric import ListView
from reservations_management.models import ReservedProducts
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required


@method_decorator(
    permission_required("reservations_management.add_reservations"), name="dispatch"
)
class MyReservationView(ListView):
    model = ReservedProducts
    template_name = "laboratory/my_reservations_list.html"
    lab_pk_field = "lab_pk"

    def get_queryset(self):
        queryset = ReservedProducts.objects.filter(
            user=self.request.user, organization__pk=self.org, laboratory__pk=self.lab
        )
        return queryset


MyReservationView.lab_pk_field = "lab_pk"
