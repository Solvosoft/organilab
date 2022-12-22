# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''

import os
from datetime import datetime, date
from django.contrib.auth.decorators import permission_required
import django_excel
from django import forms
from django.contrib import messages
from django.contrib.staticfiles import finders
from django.db.models.aggregates import Sum, Min
from django.db.models.query_utils import Q
from django.http import Http404
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404,render
from django.template.loader import get_template
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.utils.translation import gettext as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets.core import DateRangeInput, YesNoInput,Select
from laboratory.forms import H_CodeForm
from laboratory.models import Laboratory, LaboratoryRoom, Object, Furniture, ShelfObject, CLInventory, \
    OrganizationStructure,  SustanceCharacteristics,PrecursorReport
from laboratory.models import ObjectLogChange
from laboratory.utils import get_cas, get_imdg, get_molecular_formula
from laboratory.utils import get_user_laboratories
from laboratory.views.djgeneric import ListView, ReportListView, ResultQueryElement
from laboratory.views.laboratory_utils import filter_by_user_and_hcode
from organilab import settings
from laboratory.decorators import has_lab_assigned
from auth_and_perms.models import Profile
from weasyprint import HTML

from sga.forms import SearchDangerIndicationForm


#Convert html URI to absolute
def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources
    """
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources
    """
    result = finders.find(uri)
    if result:
        if not isinstance(result, (list, tuple)):
            result = [result]
        result = list(os.path.realpath(path) for path in result)
        path=result[0]
    else:
        sUrl = settings.STATIC_URL
        sRoot = settings.STATIC_ROOT
        mUrl = settings.MEDIA_URL
        mRoot = settings.MEDIA_ROOT

        if uri.startswith(mUrl):
            path = os.path.join(mRoot, uri.replace(mUrl, ""))
        elif uri.startswith(sUrl):
            path = os.path.join(sRoot, uri.replace(sUrl, ""))
        else:
            return uri

    # make sure that file exists
    if not os.path.isfile(path):
        raise Exception(
            'media URI must start with %s or %s' % (sUrl, mUrl)
        )
    return path


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


@has_lab_assigned()
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


@has_lab_assigned()
@permission_required('laboratory.do_report')
def report_labroom_building(request, *args, **kwargs):
    if 'lab_pk' in kwargs:
        rooms = get_object_or_404(
            Laboratory, pk=kwargs.get('lab_pk')).rooms.all()
    else:
        rooms = LaboratoryRoom.objects.all()

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
    }
    template = get_template('pdf/laboratoryroom_pdf.html')
    #added explicit context
    html = template.render(context=context)

    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')

    response['Content-Disposition'] = 'attachment; filename="report_laboratory.pdf"'

    return response


@has_lab_assigned()
@permission_required('laboratory.do_report')
def report_shelf_objects(request, *args, **kwargs):
    var = request.GET.get('pk')
    if var is None:
        if 'lab_pk' in kwargs:
            shelf_objects = ShelfObject.objects.filter(
                shelf__furniture__labroom__laboratory__pk=kwargs.get('lab_pk'))
        else:
            shelf_objects = ShelfObject.objects.all()
    else:
        shelf_objects = ShelfObject.objects.filter(pk=var)

    context = {
        'verbose_name': "Organilab Shelf Objects Report",
        'object_list': shelf_objects,
        'datetime': timezone.now(),
        'request': request,
        'laboratory': kwargs.get('lab_pk')
    }

    template = get_template('pdf/shelf_object_pdf.html')

    html = template.render(context=context)
    page = HTML(string=html, encoding='utf-8').write_pdf()

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


@has_lab_assigned()
@permission_required('laboratory.do_report')
def report_limited_shelf_objects(request, *args, **kwargs):
    def get_limited_shelf_objects(query):
        for shelf_object in query:
            if shelf_object.limit_reached:
                yield shelf_object

    var = request.GET.get('pk')
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

@has_lab_assigned()
@permission_required('laboratory.do_report')
def report_objects(request, *args, **kwargs):
    var = request.GET.get('pk')
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

        if 'lab_pk' in kwargs:
            filters = Q(
                shelfobject__shelf__furniture__labroom__laboratory__pk=kwargs.get('lab_pk'))
            lab_pk = kwargs.get('lab_pk')

        if 'type_id' in request.GET:

            if type_id:
                filters = filters & Q(type=type_id)

        if 'lab_pk' in kwargs and 'type_id' in request.GET:
            objects = Object.objects.filter(filters)
        else:
            objects = Object.objects.all()
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
        'laboratory': kwargs.get('lab_pk')
    }
    html = template.render(context=context)
    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')

    response['Content-Disposition'] = 'attachment; filename="report_objects.pdf"'

    return response


@has_lab_assigned()
@permission_required('laboratory.do_report')
def report_reactive_precursor_objects(request, *args, **kwargs):
    template = get_template('pdf/reactive_precursor_objects_pdf.html')
    lab = kwargs.get('lab_pk')
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
        'laboratory': lab
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


@has_lab_assigned()
@permission_required('laboratory.do_report')
def report_furniture(request, *args, **kwargs):
    var = request.GET.get('pk')
    lab = kwargs.get('lab_pk')
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
        'laboratory': lab
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


@method_decorator(has_lab_assigned(), name="dispatch")
@method_decorator(permission_required('laboratory.view_report'), name='dispatch')
class ObjectList(ListView):
    model = Object
    template_name = 'laboratory/report_object_list.html'

    def get_type(self):
        if 'type_id' in self.request.GET:
            self.type_id = self.request.GET.get('type_id', '')
            if self.type_id:
                return self.type_id
            else:
                return None
        else:
            return None

    def get_queryset(self):
        query = super(ObjectList, self).get_queryset()
        if self.get_type():
            return query.filter(
                type=self.get_type(),
                shelfobject__shelf__furniture__labroom__laboratory=self.lab)
        else:
            return query.filter(
                shelfobject__shelf__furniture__labroom__laboratory=self.lab)

    def get_context_data(self, **kwargs):
        context = super(ObjectList, self).get_context_data(**kwargs)
        context['lab_pk'] = self.kwargs.get('lab_pk')
        context['type_id'] = self.get_type()
        return context


@method_decorator(has_lab_assigned(), name="dispatch")
@method_decorator(permission_required('laboratory.view_report'), name='dispatch')
class LimitedShelfObjectList(ListView):
    model = ShelfObject
    template_name = 'laboratory/limited_shelfobject_report_list.html'

    def get_queryset(self):
        query = super(LimitedShelfObjectList, self).get_queryset()
        query = query.filter(shelf__furniture__labroom__laboratory=self.lab)
        for shelf_object in query:
            if shelf_object.limit_reached:
                yield shelf_object

    def get_context_data(self, **kwargs):
        context = super(LimitedShelfObjectList,
                        self).get_context_data(**kwargs)
        return context


@method_decorator(has_lab_assigned(), name="dispatch")
@method_decorator(permission_required('laboratory.view_report'), name='dispatch')
class ReactivePrecursorObjectList(ListView):
    model = Object
    template_name = 'laboratory/reactive_precursor_objects_list.html'

    def get_context_data(self, **kwargs):
        context = super(ReactivePrecursorObjectList,
                        self).get_context_data(**kwargs)
        context['all_labs'] = self.all_labs
        return context

    def get_queryset(self):
        try:
            self.all_labs = int(self.request.GET.get('all_labs', '0'))
        except:
            self.all_labs = 0
        query = super(ReactivePrecursorObjectList, self).get_queryset()

        query = query.filter(type=Object.REACTIVE,
                             sustancecharacteristics__is_precursor=True)
        if not self.all_labs:
            query = query.filter(
                shelfobject__shelf__furniture__labroom__laboratory=self.lab).distinct()

        for obj in query:
            clentry = CLInventory.objects.filter(
                cas_id_number=get_cas(obj, 0)).first()
            setattr(obj, 'clinventory_entry', clentry)
        return query


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

@method_decorator(has_lab_assigned(), name="dispatch")
@method_decorator(permission_required('laboratory.view_report'), name='dispatch')
class LogObjectView(ReportListView):
    model = ObjectLogChange
    paginate_by = 100
    form_class=FilterForm
    pdf_template = 'laboratory/reports/logobject_pdf.html'

    DATEFORMAT = '%d/%m/%Y' # "%m/%d/%Y"

    def format_date(self, value):
        dev = None
        try:
            dev = datetime.strptime(value, self.DATEFORMAT)
        except ValueError as e:
            pass
        return dev

    def filter_period(self, text, queryset):
        if not str:
            return queryset
        dates = text.split('-')
        if len(dates) != 2:
            return queryset
        dates[0] = self.format_date(dates[0].strip())
        dates[1] = self.format_date(dates[1].strip())
        return queryset.filter(update_time__range=dates)

    def resume_queryset(self, queryset):
        objects = set(queryset.values_list('object', flat=True))
        list_obj = []
        for obj in objects:
            ini = queryset.filter(object=obj).values('old_value')[0]['old_value']
            end = queryset.filter(object=obj).last()
            diff = queryset.filter(object=obj).aggregate(balance=Sum('diff_value'))['balance']
            list_obj.append(ResultQueryElement({'user': end.user,
                                                'laboratory': end.laboratory,
                                                'object': end.object,
                                                'update_time': end.update_time,
                                                'old_value': ini,
                                                'new_value': end.new_value,
                                                'diff_value': diff,
                                                'measurement_unit': end.measurement_unit
                                                })
                            )
        return list_obj

    def get_queryset(self):
        query = super().get_queryset().order_by('update_time')
        self.form = self.form_class(self.request.GET)
        self.form.is_valid()
        query = self.filter_period(self.form.cleaned_data['period'], query)
        if self.form.cleaned_data['precursor']:
            query = query.filter(precursor=True)
        if self.form.cleaned_data['all_laboratories']:
            query = query.filter(laboratory__in=get_user_laboratories(self.request.user) )
        else:
            query = query.filter(laboratory=self.lab)
        if self.form.cleaned_data['resume']:
            self.myqueryset = query
        return query

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form

        if self.form.cleaned_data['resume']:
            messages.info(self.request,
                          _("When resume date, we use last object for fill User, Laboratory, and Day ")
                          )
            context['object_list'] = self.resume_queryset(self.myqueryset)
        return context

    def get_book(self, context):
        book = [[str(_('User')),
                 str(_('Laboratory')),
                 str(_('Object')),
                 str(_('Day')),
                 str(_('Old')),
                 str(_('New')),
                 str(_('Difference')),
                 str(_('Unit')),
                 ]]

        for obj in context['object_list']:
            book.append([obj.user.get_full_name(),
                         str(obj.laboratory),
                         str(obj.object),
                         obj.update_time.strftime("%m/%d/%Y, %H:%M:%S"),
                         obj.old_value,
                         obj.new_value,
                         obj.diff_value,
                         str(obj.measurement_unit)
                         ])
        return book

@method_decorator(has_lab_assigned(), name="dispatch")
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
    template_name = 'laboratory/organization_reactive_presence.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_queryset(self):
        query = self.model.objects.filter(pk = self.lab) #.descendants(include_self=True)

        data = []
        add_profile_info = True
        for item in query:

            laboratories = item.laboratory_set.all().values('name', 'rooms__furniture')
            usermanagement = item.organizationusermanagement_set.all().values('users__first_name', 'users__last_name', 'users__id')
            for lab in laboratories:

                reactives = SustanceCharacteristics.objects.filter(obj__in=list(ShelfObject.objects.filter(
                    shelf__furniture=lab['rooms__furniture']
                ).values_list('object', flat=True))).exclude(cas_id_number=None).distinct()
                for user in usermanagement:
                    # Tries to acces to the user's profile if exists, otherwise an exception occured and the profile data are not going to be added
                    try:
                        profile = Profile.objects.get(user__id=user['users__id'])

                    except Profile.DoesNotExist as error:
                        add_profile_info = False

                    for reactive in reactives:
                        user_data = [lab['name'],
                                    user['users__first_name'],
                                    user['users__last_name'],
                                    reactive.obj.code,
                                    reactive.obj.name,
                                    reactive.cas_id_number,
                                    ", ".join(reactive.white_organ.all().values_list(
                                        'description', flat=True)),
                                    str(reactive.iarc) if reactive.iarc else "",
                        ]
                        if add_profile_info:
                            user_data.append(profile.id_card)
                            user_data.append(profile.job_position)
                                        
                        data.append(user_data)
                
        return data

    def get_book(self, context):
        book = [[str(_('Laboratory name')),
                 str(_('First Name')),
                 str(_('Last Name')),
                 str(_('Code')),
                 str(_('Sustance')),
                 str(_('CAS')),
                 str(_('White Organ')),
                 str(_('Carcinogenic')),
                 str(_('ID Card')),
                 str(_('Job Position'))
                 ]]+context['object_list']

        return book


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

    return render(request, 'index_organilab.html', {'form': form})