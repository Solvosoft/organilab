from django.contrib.admin.models import DELETION, CHANGE, ADDITION
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from rest_framework import status

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import OrganizationStructure
from laboratory.utils import organilab_logentry, check_user_access_kwargs_org_lab
from risk_management.forms import RiskZoneCreateForm, ZoneTypeForm, BuildingsForm, \
    RegentForm, StructureForm, IncidentReportForm
from risk_management.models import RiskZone, ZoneType, Buildings
from laboratory.views.djgeneric import ListView, CreateView, UpdateView, DeleteView, DetailView
from urllib.parse import quote
import uuid
from django.utils.translation import gettext_lazy as _


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
        kwargs['org_pk'] = self.org
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
        kwargs['org_pk'] = self.org
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

    def get_context_data(self, **kwargs):
        context = super(ZoneDetail, self).get_context_data()
        context['form_create'] = IncidentReportForm(org_pk=self.kwargs.get("org_pk",None),
                                                    prefix="create",
                                                    user=self.request.user,
                                                    risk=self.object)
        context['form_update'] = IncidentReportForm(org_pk=self.kwargs.get("org_pk",None),
                                                    prefix="update",
                                                    user=self.request.user,
                                                    risk=self.object)
        return context

@permission_required('risk_management.add_zonetype')
def add_zone_type_view(request, org_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    if not check_user_access_kwargs_org_lab(org_pk, 0, request.user):
        return JsonResponse({}, status=status.HTTP_404_NOT_FOUND)

    tipo = request.GET.get('tipo', '')
    viewid = str(uuid.uuid4())[:4]

    if request.method == 'POST':
        data= request.POST.copy()
        form =ZoneTypeForm(data)

        if form.is_valid():
            instance = form.save()
            return JsonResponse({'ok': True, 'id': instance.pk, 'text': str(instance)})

        return JsonResponse({'ok': False,
                             'title': _("There is an error in the form"),
                             'message':  render_to_string('risk_management/zone_type_add.html',
                                    context={
                                        'form': form,
                                        'tipo': quote(tipo),
                                        'viewid': viewid,
                                        'request': request
                                    }),
                             'script': 'gt_find_initialize($("#modal_zone_type_id"));'
                             })

    data = {
        'ok':  True,
        'title': _('Add a new zonetype'),
        'message': render_to_string('risk_management/zone_type_add.html',
                                    context={
                                        'form': ZoneTypeForm(),
                                        'tipo': quote(tipo),
                                        'viewid': viewid,
                                        'request':request,
                                    }),
        'script': 'gt_find_initialize($("#modal_zone_type_id"));'
    }
    return JsonResponse(data)

@permission_required('risk_management.add_buildings')
def buildings_view(request, org_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    context = {
        'org_pk': org_pk
    }
    return render(request, 'risk_management/building_list.html', context=context)

@permission_required('risk_management.add_buildings')
def buildings_actions(request, org_pk, pk=None):
    user_is_allowed_on_organization(request.user, org_pk)
    form = BuildingsForm(org_pk=org_pk)
    building = None
    title = _('Create Building')
    if pk:
        title = _('Update Building')
        building = get_object_or_404(Buildings, pk=pk)
        form = BuildingsForm(instance=building, org_pk=org_pk)
    if request.method == 'POST':
        if building:
            form = BuildingsForm(request.POST, instance=building, org_pk=org_pk)
        else:
            form = BuildingsForm(request.POST, org_pk=org_pk)

        if form.is_valid():
            building=form.save(commit=False)
            building.created_by=request.user
            building.organization=OrganizationStructure.objects.filter(pk=org_pk).first()
            building.save()
            form.save_m2m()



            return redirect(reverse('riskmanagement:buildings_list', kwargs={'org_pk': org_pk}))

    context = {
        'form':  form,
        'org_pk': org_pk,
        'title': title

    }
    return render(request, 'risk_management/buildings.html', context=context)

@permission_required('risk_management.view_regent')
def regent_view(request, org_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    context = {
        'form_create':  RegentForm(org_pk=org_pk, prefix="create"),
        'form_update':  RegentForm(org_pk=org_pk, prefix="update"),
        'org_pk': org_pk
    }
    return render(request, 'risk_management/regents.html', context=context)



@permission_required('risk_management.view_structure')
def structure_view(request, org_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    context = {
        'org_pk': org_pk
    }
    return render(request, 'risk_management/structure_list.html', context=context)

@permission_required('risk_management.add_structure')
def structure_actions(request, org_pk, pk=None):
    user_is_allowed_on_organization(request.user, org_pk)
    form = StructureForm(org_pk=org_pk)
    organization = get_object_or_404(OrganizationStructure, pk=org_pk)
    structure = None
    title = _('Create Structure')
    if pk:
        title = _('Update Structure')
        structure = get_object_or_404(Buildings, pk=pk)
        form = StructureForm(instance=structure, org_pk=org_pk)
    if request.method == 'POST':
        if structure:
            form = StructureForm(request.POST, instance=structure, org_pk=org_pk)
        else:
            form = StructureForm(request.POST, org_pk=org_pk)

        if form.is_valid():
            structure = form.save(commit=False)
            structure.created_by = request.user
            structure.organization = organization
            structure.save()
            form.save_m2m()


            return redirect(reverse('riskmanagement:structures_list', kwargs={'org_pk': org_pk}))

    context = {
        'form':  form,
        'org_pk': org_pk,
        'title': title
    }
    return render(request, 'risk_management/structure_form.html', context=context)
