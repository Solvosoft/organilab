from django.contrib.admin.models import DELETION
from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from laboratory.utils import organilab_logentry
from risk_management.forms import RiskZoneCreateForm
from risk_management.models import RiskZone


@method_decorator(permission_required('risk_management.view_riskzone'), name="dispatch")
class ListZone(ListView):
    model = RiskZone
    ordering = 'zone_type'
    ordering = ['priority', 'pk']
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        if 'q' in self.request.GET:
            q = self.request.GET['q']
            queryset = queryset.filter(Q(name__icontains=q)|Q(
                                       laboratories__name__icontains=q)).distinct()
        return queryset


    def get_context_data(self, **kwargs):
        context = super(ListZone, self).get_context_data()
        q = self.request.GET.get('q', '')

        context['q'] = q
        if q:
            context['pgparams'] = '?q=%s&'%(q,)
        else:
            context['pgparams'] = '?'
        return context

@method_decorator(permission_required('risk_management.add_riskzone'), name="dispatch")
class ZoneCreate(CreateView):
    model = RiskZone
    form_class = RiskZoneCreateForm
    success_url = reverse_lazy('riskmanagement:riskzone_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

@method_decorator(permission_required('risk_management.change_riskzone'), name="dispatch")
class ZoneEdit(UpdateView):
    model = RiskZone
    form_class = RiskZoneCreateForm
    success_url = reverse_lazy('riskmanagement:riskzone_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


@method_decorator(permission_required('risk_management.delete_riskzone'), name="dispatch")
class ZoneDelete(DeleteView):
    model = RiskZone
    success_url = reverse_lazy('riskmanagement:riskzone_list')

    def form_valid(self, form):
        success_url = self.get_success_url()
        ct = ContentType.objects.get_for_model(self.object)
        organilab_logentry(self.request.user, ct, self.object, DELETION, 'risk zone')
        self.object.delete()
        return HttpResponseRedirect(success_url)


@method_decorator(permission_required('risk_management.view_riskzone'), name="dispatch")
class ZoneDetail(DetailView):
    model = RiskZone


