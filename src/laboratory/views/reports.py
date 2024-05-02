# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''

from datetime import date

import django_excel
from django import forms
from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.db.models.aggregates import Sum, Min
from django.forms import model_to_dict
from django.http import Http404
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import get_template
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import gettext as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets.core import DateRangeInput, YesNoInput, Select
from weasyprint import HTML

from auth_and_perms.models import Profile
from laboratory.api.serializers import ShelfObjectSerialize, PrecursorSerializer
from laboratory.forms import H_CodeForm
from laboratory.models import Laboratory, LaboratoryRoom, Object, Furniture, \
    ShelfObject, CLInventory, \
    OrganizationStructure, PrecursorReport, Shelf, PrecursorReportValues
from laboratory.models import ObjectLogChange
from laboratory.utils import get_cas, get_imdg, get_molecular_formula, get_pk_org_ancestors
from laboratory.views.djgeneric import ListView, ReportListView
from laboratory.views.laboratory_utils import filter_by_user_and_hcode
from report.forms import ReportForm, ReportObjectsForm, ObjectLogChangeReportForm, \
    OrganizationReactiveForm, \
    ValidateObjectTypeForm, DiscardShelfForm
from sga.forms import SearchDangerIndicationForm

@permission_required('laboratory.do_report')
def report_shelf_objects(request, org_pk, lab_pk, pk):

    if not pk:
        if lab_pk:
            shelf_objects = ShelfObject.objects.filter(
                shelf__furniture__labroom__laboratory__pk=lab_pk)
        else:
            shelf_objects = ShelfObject.objects.all()
    else:
        shelf_objects = ShelfObject.objects.filter(pk=pk)

    context = {
        'user': request.user,
        'title': "Shelf Object Report",
        'verbose_name': "Organilab Shelf Objects Report",
        'object_list': shelf_objects,
        'datetime': timezone.now(),
        'request': request,
        'org_pk': org_pk,
        'laboratory': lab_pk,
        'domain': "file://%s" % (str(settings.MEDIA_ROOT).replace("/media/", ''),)
    }

    template = get_template('pdf/shelf_object_pdf.html')

    html = template.render(context=context)
    page = HTML(string=html, encoding='utf-8', base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(page, content_type='application/pdf')

    response['Content-Disposition'] = 'attachment; filename="report_shelf_objects.pdf"'
    return response


@permission_required('laboratory.do_report')
def report_h_code(request, *args, **kwargs):
    form = H_CodeForm(request.GET)
    q=[]
    if form.is_valid():
        q = form.cleaned_data['hcode']
    fileformat = request.GET.get('format', 'pdf')
    if fileformat in ['xls', 'xlsx', 'ods']:
        object_list = filter_by_user_and_hcode(request.user, q, function='convert_hcodereport_list')
        return django_excel.make_response_from_array(
            object_list, fileformat, file_name="hcode_report.%s" % (fileformat,))
    else:
        object_list = filter_by_user_and_hcode(request.user, q, function='convert_hcodereport_table')

    template = get_template('pdf/hcode_pdf.html')

    context = {
        'verbose_name': "H code report",
        'object_list': object_list,
        'datetime': timezone.now(),
        'request': request,
    }

    html = template.render(context=context)
    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')

    response['Content-Disposition'] = 'attachment; filename="hcode_report.pdf"'

    return response


@method_decorator(permission_required('laboratory.view_report'), name='dispatch')
class ObjectList(ListView):
    model = Object
    template_name = 'report/base_report_form_view.html'

    def get_context_data(self, **kwargs):
        context = super(ObjectList, self).get_context_data(**kwargs)
        lab_obj = get_object_or_404(Laboratory, pk=self.lab)
        type_id = ""
        title_view = _('Objects Report')
        title_by_object = {
            "0": _('Reactive Objects Report'),
            "1": _('Material Objects Report'),
            "2": _('Equipment Objects Report'),
        }

        if self.request.method == 'GET':
            if "type_id" in self.request.GET:
                id=self.request.GET["type_id"]
                if id.isalpha() or id not in title_by_object:
                    raise Http404(_("Page not found"))
            objecttypeform = ValidateObjectTypeForm(self.request.GET)

            if objecttypeform.is_valid():
                type_id = objecttypeform.cleaned_data['type_id']

        if type_id in title_by_object:
            title_view = title_by_object[type_id]

        context.update({
            'title_view': title_view,
            'report_urlnames': ['reports_objects_list'],
            'form': ReportObjectsForm(initial={
                'name': slugify(title_view + ' ' + now().strftime("%x").replace('/', '-')),
                'title': title_view,
                'organization': self.org,
                'report_name': 'report_objects',
                'laboratory': lab_obj,
                'all_labs_org': False,
                'object_type': type_id,
            })
        })
        return context


@method_decorator(permission_required('laboratory.view_report'), name='dispatch')
class LimitedShelfObjectList(ListView):
    model = ShelfObject
    template_name = 'report/base_report_form_view.html'

    def get_context_data(self, **kwargs):
        context = super(LimitedShelfObjectList,
                        self).get_context_data(**kwargs)
        title = _("Limited Shelf Objects Report")
        context['title_view'] = title
        context['report_urlnames'] = ['reports_limited_shelf_objects_list', 'reports_limited_shelf_objects']
        context['form'] = ReportForm(initial={
            'name': slugify(title +' '+ now().strftime("%x").replace('/', '-')),
            'title': title,
            'organization': self.org,
            'report_name': 'report_limit_objects',
            'laboratory': self.lab
        })
        return context


@method_decorator(permission_required('laboratory.view_report'), name='dispatch')
class ReactivePrecursorObjectList(ListView):
    model = Object
    template_name = 'report/base_report_form_view.html'

    def get_context_data(self, **kwargs):
        context = super(ReactivePrecursorObjectList,
                        self).get_context_data(**kwargs)
        lab_obj = get_object_or_404(Laboratory, pk=self.lab)
        title = _("Reactive Precursor Objects Report")
        context.update({
            'title_view': title,
            'report_urlnames': ['reactive_precursor_object_list', 'reports_reactive_precursor_objects'],
            'form': ReportForm(initial={
                'name': slugify(title + ' ' + now().strftime("%x").replace('/', '-')),
                'title': title,
                'organization': self.org,
                'report_name': 'reactive_precursor',
                'laboratory': lab_obj,
                'all_labs_org': False
            })
        })
        return context

@method_decorator(permission_required('laboratory.view_report'), name='dispatch')
class LogObjectView(ReportListView):
    model = ObjectLogChange
    template_name = "report/base_report_form_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = _("Changes on Objects Report")
        lab_obj = get_object_or_404(Laboratory, pk=self.lab)
        context.update({
            'title_view': title,
            'report_urlnames': ['object_change_logs'],
            'form': ObjectLogChangeReportForm(initial={
                'name': slugify(title + ' ' + now().strftime("%x").replace('/', '-')),
                'title': title,
                'organization': self.org,
                'report_name': 'report_objectschanges',
                'laboratory': lab_obj,
                'all_labs_org': False
            })
        })
        return context


@method_decorator(permission_required('laboratory.view_report'), name='dispatch')
class PrecursorsView(ReportListView):
    model = PrecursorReport
    template_name = 'laboratory/precursor_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['datalist'] = PrecursorReport.objects.filter(laboratory__pk=int(self.lab)).order_by('-pk')
        return context

    def get_book(self, context):
        laboratory = Laboratory.objects.get(pk=self.lab)
        month = date.today()
        month= ""
        serializer = PrecursorSerializer(data= self.request.GET)
        book=[]
        if serializer.is_valid():

            report = PrecursorReport.objects.get(pk=serializer.validated_data["pk"])
            month = report.get_month_display()
            print(month)
            first_line = [_("Name of natural or legal person: %(lab)s  N° Registration: %(consecutive)d") % {
                'lab': laboratory.name,
                'consecutive': report.consecutive
            }]
            second_line = [_("Activity to which the company is dedicated: %(activity)s") % {
                "activity":""
            }]
            third_line = [_("Report of the Month:: %(month)s of the year: %(year)d Tel: %(tel)s") % {
                "month":report.get_month_display(),
                "year": report.year,
                "tel": laboratory.phone_number
            }]
            fourth_line = [_("Responsible: %(responsible)s  Signature: %(signature)s  Position: %(position)s") % {
                "responsible": "",
                "signature": "",
                "position":""
            }]

            book = [first_line, second_line, third_line, fourth_line,[], [str(_('Name of the substance or product ')),
                                                                 str(_('Unit')),
                                                                 str(_('Final balance of the previous report')),
                                                                 str(_('Income during the month')),
                                                                 str(_('Import or local purchase invoice number that covers the entry')),
                                                                 str(_('Supplier that supplied the purchased product (in case of local purchase)')),
                                                                 str(_('Total Stock')),
                                                                 str(_('Dispatch or expense during this month')),
                                                                 str(_('Balance at the end of the month reported in this report')),
                                                                 str(_('Reason for dispatch or expense')),
                                                                 ]]
            objects = PrecursorReportValues.objects.filter(precursor_report=report)
            for obj in objects.distinct().order_by("object__name"):

                book.append([obj.object.name,
                                 obj.measurement_unit.description,
                                 obj.previous_balance,
                                 obj.new_income,
                                 obj.bills,
                                 obj.providers,
                                 obj.stock,
                                 obj.month_expense,
                                 obj.final_balance,
                                 obj.reason_to_spend
                                     ])
            self.file_name = _('Report_of_precursors_%(month)s_%(consecutive)d') % {
                "consecutive": report.consecutive,
                "month": month
            }
        return book



@method_decorator(permission_required('laboratory.view_report'), name='dispatch')
class OrganizationReactivePresenceList(ReportListView):
    model = OrganizationStructure
    template_name = 'report/base_report_form_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = _('User Reactive Exposition in Organization Report')
        context.update({
            'title_view': title,
            'laboratory': 0,
            'report_urlnames': ['organizationreactivepresence'],
            'form': OrganizationReactiveForm(initial={
                'name': slugify(title + ' ' + now().strftime("%x").replace('/', '-')),
                'title': title,
                'organization': self.org,
                'report_name': 'report_organization_reactive_list'
            }, org_pk=self.org)
        })
        return context


def getLevelClass(level):
    color = {
        0: 'default',
        1: 'danger',
        2: 'info',
        3: 'warning',
        4: 'default',
        5: 'danger',
        6: 'info'

    }
    level = level % 6
    cl="col-md-12"
    if level:
        cl="col-md-%d offset-md-%d"%(12-level, level)
    return cl, color[level]

@permission_required('laboratory.view_report')
def report_index(request, org_pk):
    org=OrganizationStructure.os_manager.filter_user(request.user).filter(pk=org_pk).first()
    if not org:
        raise Http404

    context = {
        'organization': org,
        'org_pk': org_pk
    }
    return render(request, 'laboratory/reports/report_index.html', context=context)

@method_decorator(permission_required('laboratory.do_report'), name='dispatch')
class DiscardShelfReportView(ListView):
    model = Shelf
    template_name = "report/base_report_form_view.html"

    def get_queryset(self):
        return Shelf.objects.filter(furniture__labroom__laboratory=self.lab)

    def get_context_data(self, **kwargs):
        context = super(DiscardShelfReportView, self).get_context_data(**kwargs)
        lab_obj = get_object_or_404(Laboratory, pk=self.lab)
        title = _('Waste objects by shelf report')
        initial_data = {
            'name': slugify(title + ' ' + now().strftime("%x").replace('/', '-')),
            'title': title,
            'organization': self.org,
            'report_name': 'report_waste_objects',
            'laboratory': lab_obj,
            'all_labs_org': False
        }

        context.update({
            'title_view': title,
            'form': DiscardShelfForm(initial=initial_data, org_pk=self.org)
        })
        return context
