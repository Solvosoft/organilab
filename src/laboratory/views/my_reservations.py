from django.views.generic.list import ListView
from reservations_management.models import SelectedProducts
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from laboratory.decorators import user_group_perms
from django.contrib.auth.models import User


@method_decorator(login_required, name='dispatch')
@method_decorator(user_group_perms(perm='reservations.add_reservation'), name='dispatch')
class MyReservationView(ListView):
    model = SelectedProducts
    template_name = "laboratory/my_reservations_list.html"
    
    def get_queryset(self):
        return SelectedProducts.objects.filter(user_id=self.request.user)
