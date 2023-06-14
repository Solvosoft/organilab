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


from laboratory.models import OrganizationStructure, Laboratory
from laboratory.utils import organilab_logentry, check_user_access_kwargs_org_lab
from laboratory.views import djgeneric
from risk_management.forms import IncidentReportForm
from risk_management.models import IncidentReport


@method_decorator(permission_required('risk_management.view_incidentreport'), name="dispatch")
class IncidentReportList(djgeneric.ListView):
    model = IncidentReport
    ordering = 'pk'
    ordering = ['incident_date' ]
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().filter(laboratories__pk=self.lab)

        if 'q' in self.request.GET:
            q = self.request.GET['q']
            queryset = queryset.filter(Q(short_description__icontains=q)|Q(
                laboratories__name__icontains=q
            ), laboratories__pk=self.lab)


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
            'laboratories':[self.lab]
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
         ]
    ]
    for obj in incidents:
       funobjs.append([
           obj.id,
           str(obj.creation_date),
           obj.short_description,
           obj.incident_date,
           obj.causes,
           obj.infraestructure_impact,
           obj.people_impact,
           obj.environment_impact,
           obj.result_of_plans,
           obj.mitigation_actions,
           obj.recomendations,
           ",".join([x.name for x in obj.laboratories.all()]),
            ])
    content[_('Incidents')] = funobjs

    return content


@permission_required('laboratory.do_report')
def report_incidentreport(request, org_pk, lab_pk, pk):

    if not check_user_access_kwargs_org_lab(org_pk, lab_pk, request.user):
        return JsonResponse({}, status=status.HTTP_404_NOT_FOUND)

    lab = get_object_or_404(Laboratory, pk=lab_pk)
    filters = {'laboratories__in': [lab]}

    if pk:
        filters = {'pk': pk}

    incidentreport = IncidentReport.objects.filter(**filters)

    fileformat = request.GET.get('format', 'pdf')
    if fileformat in ['xls', 'xlsx', 'ods']:
        return django_excel.make_response_from_book_dict(
            make_book_incidentreport(incidentreport), fileformat, file_name="incident.%s" % (fileformat,))

    template = get_template('risk_management/incidentreport_pdf.html')

    context = {
        'verbose_name': "Incident report",
        'object_list': incidentreport,
        'datetime': timezone.now(),
        'request': request,
        'laboratory': lab
    }

    html = template.render(context=context)
    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')

    response['Content-Disposition'] = 'attachment; filename="incident_report.pdf"'
    return response
