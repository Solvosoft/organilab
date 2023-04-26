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
from laboratory.forms import H_CodeForm
from laboratory.models import Laboratory, LaboratoryRoom, Object, Furniture, ShelfObject, CLInventory, \
    OrganizationStructure, PrecursorReport
from laboratory.models import ObjectLogChange
from laboratory.utils import get_cas, get_imdg, get_molecular_formula, get_pk_org_ancestors
from laboratory.views.djgeneric import ListView, ReportListView
from laboratory.views.laboratory_utils import filter_by_user_and_hcode
from report.forms import ReportForm, ReportObjectsForm, ObjectLogChangeReportForm, OrganizationReactiveForm, \
    ValidateObjectTypeForm
from sga.forms import SearchDangerIndicationForm


def make_book_organization_laboratory(objects):
    dev = [
        [_("Name"), _("Phone"), _("Location"), _(
            "Profile"), _('Phones'), _('Emails')]
    ]
    for object in objects:
        profile = ""
        phones = ""
        emails = ""

        profiles_list = Profile.objects.filter(laboratories__in=[object])

        for pr in profiles_list:
            if profile != "":
                profile += " \n"
                phones += " \n"
                emails += " \n"
            profile += pr.user.get_full_name()
            phones += pr.phone_number
            emails += pr.user.email
        dev.append([
            object.name,
            object.phone_number,
            object.location,
            profile,
            phones,
            emails,
        ])
    return dev



@permission_required('laboratory.do_report')
def report_organization_building(request, *args, **kwargs):
    var = request.GET.get('organization')
    if var:  # when have user selecting org
        org = get_object_or_404(OrganizationStructure, pk=var)
        organizations_child = OrganizationStructure.os_manager.filter_user(
            request.user)
        if org in organizations_child:  # user have perm on that organization ?
            organizations_child = list(org.descendants(include_self=True).values_list('pk', flat=True))
            labs = Laboratory.objects.filter(
                organization__in=organizations_child)
        else:
            if request.user.is_superuser:
                organizations_child = list(OrganizationStructure.os_manager.get_children(
                    var).values_list('pk', flat=True))
                labs = Laboratory.objects.filter(
                    organization__in=organizations_child)
            else:
                labs = Laboratory.objects.none()
    else:  # when haven't user selecting org
        organizations_child = list(OrganizationStructure.os_manager.filter_user(
            request.user).values_list('pk', flat=True))

        if organizations_child:
            labs = Laboratory.objects.filter(
                organization__in=organizations_child)
        else:
            if request.user.is_superuser:
                labs = Laboratory.objects.all()
            else:
                labs = Laboratory.objects.none()

    fileformat = request.GET.get('format', 'pdf')
    if fileformat in ['xls', 'xlsx', 'ods']:
        return django_excel.make_response_from_array(
            make_book_organization_laboratory(labs), fileformat, file_name="Laboratories.%s" % (fileformat,))

    context = {
        #title of the report in verbose_name variable
        'verbose_name': "Organization laboratory report",
        'object_list': labs,
        'datetime': timezone.now(),
        'request': request,
        'laboratory': kwargs.get('lab_pk'),
        'org_pk': kwargs.get('org_pk'),
    }

    template = get_template('pdf/organizationlaboratory_pdf.html')
    html = template.render(context=context)
    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')

    response['Content-Disposition'] = 'attachment; filename="report_organization_libraries.pdf"'
    return response


def make_book_laboratory(rooms):

    content = {}
    for labroom in rooms:
        labobj = [[
            _("Furniture"),
            _("Shelf"),
            _("Code"),
            _("Name"),
            _("Quantity"),
            _("Units"),
            _("Object type"),
            _("CAS ID"),
            _("IMDG code")
        ]]

        for furniture in labroom.furniture_set.all():
            for obj in furniture.get_objects():
                labobj.append([
                    furniture.name,
                    obj.shelf.name,
                    obj.object.code,
                    obj.object.name,
                    obj.quantity,
                    obj.get_measurement_unit_display(),
                    obj.object.get_type_display(),
                    get_cas(obj.object,""),
                    str(get_imdg(obj.object,""))
                ])
        if labobj:
            content[labroom.name] = labobj

    return content



@permission_required('laboratory.do_report')
def report_labroom_building(request, *args, **kwargs):
    org=None
    if 'lab_pk' in kwargs:
        rooms = get_object_or_404(
            Laboratory, pk=kwargs.get('lab_pk')).laboratoryroom_set.all()
    else:
        rooms = LaboratoryRoom.objects.all()
    if 'org_pk' in kwargs:
        org=kwargs.get('org_pk')
    fileformat = request.GET.get('format', 'pdf')
    if fileformat in ['xls', 'xlsx', 'ods']:
        return django_excel.make_response_from_book_dict(
            make_book_laboratory(rooms), fileformat, file_name="Laboratories.%s" % (fileformat,))


    context = {
        #set your report title in verbose_name
        'verbose_name': "Organilab Laboratory Report",
        'object_list': rooms,
        'datetime': timezone.now(),
        'request': request,
        'laboratory': kwargs.get('lab_pk'),
        'org_pk': org
    }
    template = get_template('pdf/laboratoryroom_pdf.html')
    #added explicit context
    html = template.render(context=context)

    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')

    response['Content-Disposition'] = 'attachment; filename="report_laboratory.pdf"'

    return response



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


def make_book_limited_reached(objects):
    dev = [
        [_("Code"), _("Name"), _("Quantity"), _(
            "Limit quantity"), _("Mesurement units")]
    ]
    for object in objects:
        dev.append([
            object.object.code,
            object.object.name,
            object.quantity,
            object.limit_quantity,
            object.get_measurement_unit_display()
        ])
    return dev



@permission_required('laboratory.do_report')
def report_limited_shelf_objects(request, *args, **kwargs):
    def get_limited_shelf_objects(query):
        for shelf_object in query:
            if shelf_object.limit_reached:
                yield shelf_object

    var = request.GET.get('pk')
    org = kwargs.get('org_pk')

    if var is None:
        if 'lab_pk' in kwargs:
            shelf_objects = ShelfObject.objects.filter(
                shelf__furniture__labroom__laboratory__pk=kwargs.get('lab_pk'))
        else:
            shelf_objects = ShelfObject.objects.all()
    else:
        shelf_objects = ShelfObject.objects.filter(pk=var)

    shelf_objects = get_limited_shelf_objects(shelf_objects)

    template = get_template('pdf/shelf_object_pdf.html')

    fileformat = request.GET.get('format', 'pdf')
    if fileformat in ['xls', 'xlsx', 'ods']:
        return django_excel.make_response_from_array(
            make_book_limited_reached(shelf_objects), fileformat, file_name="Laboratories.%s" % (fileformat,))

    context = {
        'verbose_name': "Limited shelf objects",
        'object_list': shelf_objects,
        'datetime': timezone.now(),
        'request': request,
        'org_pk': org,
        'laboratory': kwargs.get('lab_pk')
    }
    html = template.render(context=context)

    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')

    response['Content-Disposition'] = 'attachment; filename="report_limited_shelf_objects.pdf"'
    return response


def make_book_objects(objects, summary=False, type_id=None, lab_pk=None):

    description = [
        _("Laboratory"), _("Code"), _("Name"), _("Type"), _("Quantity total"), _('Measurement units')
    ]

    if type_id == '0':
        description += [
            _("Molecular formula"),
            _("CAS id number"),
            _("Is precursor?"),
            _("IMDG type")
        ]
    content = {
        'objects': [
            description,
    ]
    }
    objects = objects.annotate(quantity_total=Sum('shelfobject__quantity'),
                               measurement_unit=Min('shelfobject__measurement_unit'))
    lab = Laboratory.objects.filter(pk=lab_pk).first() if lab_pk else None
    for object in objects:
        obj_info = [
            str(lab) if lab else '',
            object.code,
            object.name,
            object.get_type_display(),
            object.quantity_total,
            ShelfObject.get_units(object.measurement_unit)]
        if type_id == '0':
            obj_info += [
                get_molecular_formula(object),
                get_cas(object, ''),
                object.is_precursor,
                str(get_imdg(object, ''))]

        content['objects'].append(obj_info)
        if not summary:
            shelfquery = object.shelfobject_set.filter(
                shelf__furniture__labroom__laboratory__pk=lab_pk) if lab_pk else object.shelfobject_set.all()
            for shelfobj in shelfquery:
                content['objects'].append(['', shelfobj.shelf.furniture.name,
                                           shelfobj.shelf.name,
                                           shelfobj.quantity,
                                           shelfobj.get_measurement_unit_display()
                                           ])
    return content


@permission_required('laboratory.do_report')
def report_objects(request, *args, **kwargs):
    var = request.GET.get('pk')
    org = kwargs.get('org_pk')
    filters = {}

    try:
        detail = bool(int(request.GET.get('details', 0)))
    except:
        detail = False
    lab_pk = None
    namef = 'objects'
    type_id = request.GET.get('type_id', '')
    typename=dict(Object.TYPE_CHOICES)
    type_name = typename[type_id] if type_id in typename else ''
    if 'lab_pk' in kwargs:
        lab = Laboratory.objects.filter(pk=kwargs.get('lab_pk')).first()
        if lab:
            namef = slugify(str(lab))+"_"+type_name+"_"+str('resume' if detail else "detail")
    if var is None:

        if org:
            filters['organization__in'] = get_pk_org_ancestors(org)
            filters['is_public'] =True

        if 'type_id' in request.GET:
            filters['type'] = request.GET.get('type_id')


        if filters:
            objects = Object.objects.filter(**filters)
        else:
            objects = Object.objects.none()
    else:
        objects = Object.objects.filter(pk=var)


    fileformat = request.GET.get('format', 'pdf')
    if fileformat in ['xls', 'xlsx', 'ods']:
        return django_excel.make_response_from_book_dict(
            make_book_objects(objects, summary=detail, type_id=type_id, lab_pk=lab_pk), fileformat,
            file_name="%s.%s" % (namef, fileformat,))


    for obj in objects:
        clentry = CLInventory.objects.filter(
            cas_id_number=get_cas(obj, 0)).first()
        setattr(obj, 'clinventory_entry', clentry)

    template = get_template('pdf/object_pdf.html')
    verbose_name =  'Reactives report'
    if type_id == "1": verbose_name = 'Materials report'
    if type_id == "2": verbose_name = 'Equipments report'
    context = {
        'verbose_name': verbose_name,
        'object_list': objects,
        'datetime': timezone.now(),
        'request': request,
        'laboratory': kwargs.get('lab_pk'),
        'org_pk': org
    }
    html = template.render(context=context)
    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')

    response['Content-Disposition'] = 'attachment; filename="report_objects.pdf"'

    return response


@permission_required('laboratory.do_report')
def report_reactive_precursor_objects(request, *args, **kwargs):

    template = get_template('pdf/reactive_precursor_objects_pdf.html')
    lab = kwargs.get('lab_pk')
    org = kwargs.get('org_pk')

    try:
        all_labs = int(request.GET.get('all_labs', '0'))
    except:
        all_labs = 0
    if lab and not all_labs:
        rpo = Object.objects.filter(
            shelfobject__shelf__furniture__labroom__laboratory__pk=lab)
    else:
        rpo = Object.objects.all()

    rpo = rpo.filter(type=Object.REACTIVE, sustancecharacteristics__is_precursor=True)

    for obj in rpo:
        clentry = CLInventory.objects.filter(
            cas_id_number=get_cas(obj, 0)).first()
        setattr(obj, 'clinventory_entry', clentry)

    fileformat = request.GET.get('format', 'pdf')
    if fileformat in ['xls', 'xlsx', 'ods']:
        return django_excel.make_response_from_book_dict(
            make_book_objects(rpo, summary=True, type_id='0'), fileformat, file_name="reactive_precursor.%s" % (fileformat,))

    context = {
        'verbose_name': "Reactive precursor objects",
        'rpo': rpo,
        'datetime': timezone.now(),
        'request': request,
        'laboratory': lab,
        'org_pk': org,
    }

    html = template.render(context=context)
    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')

    response['Content-Disposition'] = 'attachment; filename="report_reactive_precursor_objects.pdf"'

    return response



def make_book_furniture_objects(furnitures):
    content = {}
    for furniture in furnitures:
        funobjs = [
            [_("Shelf"),
                _("Code"),
                _("Name"),
                _("Quantity"),
                _("Limit Quantity"),
                _("Units"),
             ]
        ]
        for shelf in furniture.shelf_set.all():
            for obj in shelf.shelfobject_set.all():
                funobjs.append([

                    obj.shelf.name,
                    obj.object.code,
                    obj.object.name,
                    obj.quantity,
                    obj.limit_quantity,
                    obj.get_measurement_unit_display(),
                ])
        content[furniture.name] = funobjs

    return content



@permission_required('laboratory.do_report')
def report_furniture(request, *args, **kwargs):
    var = request.GET.get('pk')
    lab = kwargs.get('lab_pk')
    org = kwargs.get('org_pk')

    if var is None:
        furniture = Furniture.objects.filter(
            labroom__laboratory__pk=lab)
    else:
        furniture = Furniture.objects.filter(pk=var)

    fileformat = request.GET.get('format', 'pdf')
    if fileformat in ['xls', 'xlsx', 'ods']:
        return django_excel.make_response_from_book_dict(
            make_book_furniture_objects(furniture), fileformat, file_name="Furniture.%s" % (fileformat,))


    context = {
        'verbose_name': "Organilab Summary Furniture Report",
        'object_list': furniture,
        'datetime': timezone.now(),
        'request': request,
        'laboratory': lab,
        'org_pk': org
    }

    template = get_template('pdf/summaryfurniture_pdf.html')
    html = template.render(context=context)
    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')

    response['Content-Disposition'] = 'attachment; filename="furniture_report.pdf"'

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
        title_by_object = {
            "0": _('Reactive Objects Report'),
            "1": _('Material Objects Report'),
            "2": _('Equipment Objects Report'),
        }
        objecttypeform = ValidateObjectTypeForm(self.request.GET)

        if objecttypeform.is_valid():
            type_id = objecttypeform.cleaned_data['type_id']

        if type_id in title_by_object:
            title_view = title_by_object[type_id]
        else:
            title_view = _('Objects Report')

        context.update({
            'title_view': title_view,
            'report_urlnames': ['reports_objects_list', 'reports_objects'],
            'form': ReportObjectsForm(initial={
                'name': title_view + ' ' + now().strftime("%x").replace('/', '-'),
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
            'name': title +' '+ now().strftime("%x").replace('/', '-'),
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
            'report_urlnames': ['reports_objects', 'reactive_precursor_object_list', 'reports_reactive_precursor_objects'],
            'form': ReportForm(initial={
                'name': title + ' ' + now().strftime("%x").replace('/', '-'),
                'title': title,
                'organization': self.org,
                'report_name': 'reactive_precursor',
                'laboratory': lab_obj,
                'all_labs_org': False
            })
        })
        return context


class FilterForm(GTForm, forms.Form):
    period = forms.CharField(widget=DateRangeInput, required=False,label=_('Period'))
    precursor = forms.BooleanField(widget=YesNoInput,  required=False,label=_('Precursor'))
    all_laboratories = forms.BooleanField(widget=YesNoInput, required=False,label=_('All labs'))
    resume = forms.BooleanField(widget=YesNoInput, required=False,label=_('Resume'))
    format = forms.ChoiceField(widget=Select,choices=(
        ('html', _('On screen')),
        ('pdf', _('PDF')),
        ('xls', 'XSL'),
        ('xlsx', 'XLSX'),
        ('ods', 'ODS')
    ), required=False,label=_('Format'))

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
                'name': title + ' ' + now().strftime("%x").replace('/', '-'),
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
        context['datalist'] = PrecursorReport.objects.filter(laboratory__pk=int(self.lab))
        return context

    def get_book(self, context):
        laboratory = Laboratory.objects.get(pk=self.lab)
        month = date.today()
        month=month.strftime("%B")
        first_line = [
            _("Coordinator"), laboratory.coordinator, _('Unit'), laboratory.unit, _('#Consecutivo'), str(self.request.GET.get('consecutive')),
        ]
        second_line = [
            _("Laboratorio o centro de trabajo"), laboratory.name, _('Month'), _(month),
        ]
        third_line = [
            _("Email"), laboratory.email, _('Phone'), laboratory.phone_number,
        ]
        book = [first_line, second_line, third_line,[], [str(_('Nombre de la sustancia o producto')),
                                                      str(_('Unid')),
                                                      str(_('Saldo final de reporte anterior')),
                                                      str(_('Ingresos durante el mes')),
                                                      str(_('Numero de factura')),
                                                      str(_('Proveedor')),
                                                      str(_('Total de existencias')),
                                                      str(_('Gasto durante el mes')),
                                                      str(_('Saldo al final del mes reportado en este informe')),
                                                      str(_('Razon de gasto o despacho')),
                                                      str(_('Asunto')),
                                                      ]]
        month = int(self.request.GET.get('month'))
        year = int(self.request.GET.get('year'))

        object_list = ObjectLogChange.objects.values('object','measurement_unit__key','object__name', 'laboratory') \
            .filter(laboratory=self.lab, precursor=True,
                    update_time__month=month,type_action__lte=1, update_time__year=year).annotate(amount=Sum('diff_value'), )

        for obj in object_list:

            providers = ', '.join(self.get_providers(month, year, obj['object']))
            subjects = ', '.join(self.get_subjects(month, year, obj['object']))
            last_month_amount = float(self.get_pre_amount(month, year, obj['object']))
            notes = ', '.join(self.get_notes(month, year, obj['object']))
            bills = ', '.join(self.get_bills(month, year, obj['object']))
            amount_spend = abs(self.get_amount_spend(month, year, obj['object']))

            book.append([str(obj['object__name']),
                         str(obj['measurement_unit__key']),
                         last_month_amount,
                         str(obj['amount']),
                         bills,
                         providers,
                         last_month_amount+float(obj['amount']),
                         amount_spend,
                         obj['amount']-amount_spend,
                         notes,
                         subjects,
                         ])
        return book

    def get_pre_month(self, month, year):

        if month == 1:
            month = 12
            year = year-1
        else:
            month = month-1

        return {'month': month,
                'year': year}

    def get_providers(self, month, year, obj):
        providers = ObjectLogChange.objects.values('object', 'provider__name', 'laboratory').\
            filter(laboratory=self.lab, precursor=True, object__pk=obj, update_time__month=int(month),
                   update_time__year=int(year))
        data = []
        for p in providers:
            if p['provider__name'] is not None:
                data.append(p['provider__name'])

        return set(data)

    def get_subjects(self, month, year, obj):
        subjects = ObjectLogChange.objects.values('object', 'subject', 'laboratory').\
            filter(laboratory=self.lab, precursor=True, object__pk=obj, update_time__month=int(month),
                   update_time__year=int(year))
        data = []
        for s in subjects:
            if s['subject'] is not None:
                data.append(s['subject'])

        return set(data)

    def get_notes(self, month, year, obj):
        notes = ObjectLogChange.objects.values('object', 'note', 'laboratory').\
            filter(laboratory=self.lab, precursor=True, object__pk=obj, update_time__month=int(month),
                   update_time__year=int(year))
        data = []
        for n in notes:
            if n['note'] is not None and len(n['note']) > 0:
                data.append(n['note'])

        return set(data)

    def get_bills(self, month, year, obj):
        bills = ObjectLogChange.objects.values('object', 'bill', 'laboratory').\
            filter(laboratory=self.lab, precursor=True, object__pk=obj, update_time__month=int(month),
                   update_time__year=int(year))
        data = []
        for b in bills:
            if b['bill'] is not None:
                data.append(b['bill'])

        return set(data)

    def get_pre_amount(self, month, year, obj):

        date = self.get_pre_month(month,year)
        amount = 0
        object_list = ObjectLogChange.objects.values('object', 'new_value','laboratory') \
            .filter(laboratory=self.lab, precursor=True,object=obj,
                    update_time__month=date['month'], update_time__year=date['year']).last()

        if object_list is not None:
            amount = object_list['new_value']

        return amount

    def get_amount_spend(self, month, year, obj):
        amount = 0
        object_list = ObjectLogChange.objects.values('object','laboratory') \
            .filter(laboratory=self.lab, precursor=True,object=obj,
                    update_time__month=month, type_action=2, update_time__year=year).annotate(spend=Sum('diff_value'))

        if len(object_list) > 0:
            amount=object_list[0]['spend']

        return amount


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
                'name': title + ' ' + now().strftime("%x").replace('/', '-'),
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



def search_danger_indication_report(request):
    if request.method == "POST":
        form = SearchDangerIndicationForm(request.POST)

        if form.is_valid():
            hcodes_list = form.cleaned_data['codes']
            prudence_advices = set([y for x in hcodes_list for y in x.prudence_advice.all()])
            pictograms = set([y for x in hcodes_list for y in x.pictograms.all() if y.name != "Sin Pictograma"])
            warning_word = max(hcodes_list, key=lambda x: x.warning_words.weigth).warning_words
            return render(request, 'danger_indication_info.html', {'hcodes_list': hcodes_list,
                                                                   'prudence_advices': prudence_advices,
                                                                   'warning_word': warning_word,
                                                                   'pictograms': pictograms})

    else:
        form = SearchDangerIndicationForm()

    return render(request, 'laboratory/reports/report_danger_indication.html', {'form': form})