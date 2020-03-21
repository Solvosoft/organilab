from django.shortcuts import render

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from risk_management.forms import RiskZoneCreateForm
from risk_management.models import RiskZone


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

class ZoneCreate(CreateView):
    model = RiskZone
    form_class = RiskZoneCreateForm
    success_url = reverse_lazy('riskmanagement:riskzone_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class ZoneEdit(UpdateView):
    model = RiskZone
    form_class = RiskZoneCreateForm
    success_url = reverse_lazy('riskmanagement:riskzone_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class ZoneDelete(DeleteView):
    model = RiskZone
    success_url = reverse_lazy('riskmanagement:riskzone_list')
