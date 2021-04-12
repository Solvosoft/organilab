from django.views.generic.list import ListView
from reservations_management.models import ReservedProducts
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required


@method_decorator(permission_required('reservations_management.add_reservations'), name='dispatch')
class MyReservationView(ListView):
    model = ReservedProducts
    template_name = "laboratory/my_reservations_list.html"
    
    def get_queryset(self):
        return ReservedProducts.objects.filter(user_id=self.request.user)
