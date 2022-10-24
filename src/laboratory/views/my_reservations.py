from django.views.generic.list import ListView
from reservations_management.models import ReservedProducts
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required


@method_decorator(permission_required('reservations_management.add_reservations'), name='dispatch')
class MyReservationView(ListView):
    model = ReservedProducts
    template_name = "laboratory/my_reservations_list.html"
    lab_pk_field='pk'

    def get_queryset(self):

        return ReservedProducts.objects.filter(user_id=self.request.user)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(MyReservationView, self).get_context_data()
        context['labpk'] = self.kwargs['pk']

        return context

MyReservationView.lab_pk_field='pk'