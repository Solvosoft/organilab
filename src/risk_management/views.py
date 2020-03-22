from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from laboratory.decorators import user_group_perms
from risk_management.forms import RiskZoneCreateForm
from risk_management.models import RiskZone


@method_decorator(login_required, name='dispatch')
@method_decorator(user_group_perms(perm='risk_management.view_riskzone'), name='dispatch')
class ListZone(ListView):
    model = RiskZone
    ordering = 'zone_type'
    ordering = ['priority', 'pk']
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        if 'q' in self.request.GET:
            q = self.request.GET['q']
            queryset = queryset.filter(name__icontains=q)
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

@method_decorator(login_required, name='dispatch')
@method_decorator(user_group_perms(perm='risk_management.add_riskzone'), name='dispatch')
class ZoneCreate(CreateView):
    model = RiskZone
    form_class = RiskZoneCreateForm
    success_url = reverse_lazy('riskmanagement:riskzone_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

@method_decorator(login_required, name='dispatch')
@method_decorator(user_group_perms(perm='risk_management.change_riskzone'), name='dispatch')
class ZoneEdit(UpdateView):
    model = RiskZone
    form_class = RiskZoneCreateForm
    success_url = reverse_lazy('riskmanagement:riskzone_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

@method_decorator(login_required, name='dispatch')
@method_decorator(user_group_perms(perm='risk_management.delete_riskzone'), name='dispatch')
class ZoneDelete(DeleteView):
    model = RiskZone
    success_url = reverse_lazy('riskmanagement:riskzone_list')

@method_decorator(login_required, name='dispatch')
@method_decorator(user_group_perms(perm='risk_management.view_riskzone'), name='dispatch')
class ZoneDetail(DetailView):
    model = RiskZone


