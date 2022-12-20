from django.contrib.admin.models import DELETION, CHANGE, ADDITION
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

from laboratory.models import OrganizationStructure
from laboratory.utils import organilab_logentry
from risk_management.forms import RiskZoneCreateForm
from risk_management.models import RiskZone
from laboratory.views.djgeneric import ListView, CreateView, UpdateView, DeleteView, DetailView


@method_decorator(permission_required('risk_management.view_riskzone'), name="dispatch")
class ListZone(ListView):
    model = RiskZone
    ordering = 'zone_type'
    ordering = ['priority', 'pk']
    paginate_by = 20

    def get_queryset(self):
        org = self.kwargs['org_pk']

        queryset = super().get_queryset().filter(organization__pk=org)
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        dev = super().form_valid(form)
        risk_zone= form.save(commit=False)
        org = self.kwargs['org_pk']
        org = OrganizationStructure.objects.filter(pk=org).first()
        risk_zone.organization=org
        risk_zone.created_by=self.request.user
        risk_zone.save()
        organilab_logentry(self.request.user, self.object, ADDITION, relobj=list(self.object.laboratories.all()))
        return dev
    def get_success_url(self, **kwargs):
        org_pk = self.kwargs['org_pk']
        success_url = reverse_lazy('riskmanagement:riskzone_list', kwargs={'org_pk': org_pk})
        return success_url

@method_decorator(permission_required('risk_management.change_riskzone'), name="dispatch")
class ZoneEdit(UpdateView):
    model = RiskZone
    form_class = RiskZoneCreateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        dev = super().form_valid(form)
        organilab_logentry(self.request.user, self.object, CHANGE, relobj=list(self.object.laboratories.all()))
        return dev
    def get_success_url(self, **kwargs):
        org_pk = self.org
        success_url = reverse_lazy('riskmanagement:riskzone_list', kwargs={'org_pk': org_pk})
        return success_url
@method_decorator(permission_required('risk_management.delete_riskzone'), name="dispatch")
class ZoneDelete(DeleteView):
    model = RiskZone

    def form_valid(self, form):
        success_url = self.get_success_url()
        organilab_logentry(self.request.user, self.object, DELETION, relobj=list(self.object.laboratories.all()))
        self.object.delete()
        return HttpResponseRedirect(success_url)

    def get_success_url(self, **kwargs):
        org_pk = self.org
        success_url = reverse_lazy('riskmanagement:riskzone_list', kwargs={'org_pk': org_pk})
        return success_url

@method_decorator(permission_required('risk_management.view_riskzone'), name="dispatch")
class ZoneDetail(DetailView):
    model = RiskZone


