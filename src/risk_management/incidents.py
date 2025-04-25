import re

import django_excel
from django.contrib.admin.models import DELETION, CHANGE, ADDITION
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from rest_framework import status
from weasyprint import HTML
from django.conf import settings

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import OrganizationStructure, Laboratory
from laboratory.utils import organilab_logentry, check_user_access_kwargs_org_lab
from laboratory.views import djgeneric
from risk_management.forms import IncidentReportForm
from risk_management.models import IncidentReport, Buildings, RiskZone


@method_decorator(permission_required('risk_management.view_incidentreport'), name="dispatch")
class IncidentReportList(djgeneric.ListView):
    model = IncidentReport
    ordering = 'pk'
    ordering = ['incident_date' ]
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().filter(buildings=self.building)
        filter_search = self.request.GET.get('q', None)
        if filter_search:
            queryset = queryset.filter(Q(short_description__icontains=filter_search)|Q(
                laboratories__name__icontains=filter_search
            ), buildings__pk=self.building.pk)


        return queryset


    def get_context_data(self, **kwargs):
        context = super(IncidentReportList, self).get_context_data()
        q = self.request.GET.get('q', '')

        context['q'] = q
        if q:
            context['pgparams'] = '?q=%s&'%(q,)
        else:
            context['pgparams'] = '?'
        return context

@method_decorator(permission_required('risk_management.add_incidentreport'), name="dispatch")
class IncidentReportCreate(djgeneric.CreateView):
    model = IncidentReport
    form_class = IncidentReportForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['org_pk'] = self.org
        kwargs['initial']={
            'laboratories':[self.building.laboratories.all()]
        }
        return kwargs

    def form_valid(self, form):
        dev = super().form_valid(form)
        incident = form.save(commit=False)
        org = self.org
        org = OrganizationStructure.objects.filter(pk=org).first()
        incident.organization = org
        incident.created_by = self.request.user
        incident.save()
        organilab_logentry(self.request.user, self.object, ADDITION, relobj=list(self.object.laboratories.all()))
        return dev

    def get_success_url(self, **kwargs):
        org_pk = self.org
        success_url = reverse_lazy('riskmanagement:riskzone_list', kwargs={'org_pk': org_pk})
        return success_url

@method_decorator(permission_required('risk_management.change_incidentreport'), name="dispatch")
class IncidentReportEdit(djgeneric.UpdateView):
    model = IncidentReport
    form_class = IncidentReportForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['org_pk'] = self.org
        kwargs['initial']={
            'laboratories':[self.lab]
        }
        return kwargs

    def form_valid(self, form):
        dev = super().form_valid(form)
        organilab_logentry(self.request.user, self.object, CHANGE, relobj=list(self.object.laboratories.all()))
        return dev

    def get_success_url(self, **kwargs):
        org_pk = self.org
        success_url = reverse_lazy('riskmanagement:riskzone_list', kwargs={'org_pk': org_pk})
        return success_url

@method_decorator(permission_required('risk_management.delete_incidentreport'), name="dispatch")
class IncidentReportDelete(djgeneric.DeleteView):
    model = IncidentReport

    def form_valid(self, form):
        success_url = self.get_success_url()
        organilab_logentry(self.request.user, self.object, DELETION, relobj=list(self.object.laboratories.all()))
        self.object.delete()
        return HttpResponseRedirect(success_url)
    def get_success_url(self, **kwargs):
        org_pk = self.org
        success_url = reverse_lazy('riskmanagement:riskzone_list', kwargs={'org_pk': org_pk})
        return success_url

@method_decorator(permission_required('risk_management.view_incidentreport'), name="dispatch")
class IncidentReportDetail(djgeneric.DetailView):
    model = IncidentReport

def make_book_incidentreport(incidents):
    content = {}
    funobjs = [
        [
_('Identificador'),
_('Creation Date'),
_('Short Description'),
_('Incident Date'),
_('Causes'),
_('Infraestructure impact'),
_('People impact'),
_('Environment impact'),
_('Result of plans'),
_('Mitigation actions'),
_('Recomendations'),
_('Laboratories'),
 _('Buildings'),
         ]
    ]
    for obj in incidents:
       funobjs.append([
           obj.id,
           str(obj.creation_date),
           obj.short_description,
           obj.incident_date,
           re.sub(r'<.*?>', '', obj.causes),
           re.sub(r'<.*?>', '', obj.infraestructure_impact),
           re.sub(r'<.*?>', '', obj.people_impact),
           re.sub(r'<.*?>', '', obj.result_of_plans),
           re.sub(r'<.*?>', '', obj.mitigation_actions),
           re.sub(r'<.*?>', '', obj.recomendations),
           ", ".join([x.name for x in obj.laboratories.all()]),
           ", ".join([x.name for x in obj.buildings.all()]),
            ])
    content[_('Incidents')] = funobjs

    return content


@permission_required('laboratory.do_report')
def report_incidentreport(request, org_pk, risk_pk, pk):
    user_is_allowed_on_organization(request.user, org_pk)

    risks = get_object_or_404(RiskZone, pk=risk_pk)
    filters = {'risk_zone__in': [risks]}

    if pk:
        filters = {'pk': pk}

    incidentreport = IncidentReport.objects.filter(**filters)

    fileformat = request.GET.get('format', 'pdf')
    if fileformat in ['xls', 'xlsx', 'ods']:
        return django_excel.make_response_from_book_dict(
            make_book_incidentreport(incidentreport), fileformat, file_name="incident.%s" % (fileformat,))

    template = get_template('risk_management/incidentreport_pdf.html')

    context = {
        'object_list': incidentreport,
        'datetime': timezone.now(),
        'user': request.user,
        'title': _("Incident report in the risk zone %s")% risks.name,
    }

    html = template.render(context=context)
    page = HTML(string=html, base_url=request.build_absolute_uri(),
                encoding='utf-8').write_pdf()
    response = HttpResponse(page, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="incident_report.pdf"'
    return response
