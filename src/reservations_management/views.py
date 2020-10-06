from django.shortcuts import render
from django.views.generic.list import ListView

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from laboratory.decorators import user_group_perms

from .models import Reservations

# Create your views here.

@method_decorator(login_required, name='dispatch')
@method_decorator(user_group_perms(perm='laboratory.add_objectfeatures'), name='dispatch')
class ReservationsListView(ListView):
    model = Reservations
    paginate_by = 10 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reservations'] = Reservations.objects.filter(laboratory__profile__user_id=self.request.user.id)
        return context