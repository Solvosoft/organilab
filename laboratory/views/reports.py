# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''
from __future__ import unicode_literals

from django.db.models.query_utils import Q
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.utils import timezone
from django.utils.decorators import method_decorator
from weasyprint import HTML
from django.utils.translation import ugettext as _

from laboratory.models import Laboratory, LaboratoryRoom, Object, Furniture, ShelfObject, CLInventory, OrganizationStructure, PrincipalTechnician
from laboratory.views.djgeneric import ListView
from laboratory.decorators import user_lab_perms
import django_excel
from django.db.models.aggregates import Sum, Min


def make_book_organization_laboratory(objects):
    dev=[
        [_("Name"), _("Phone"), _("Location"),_("Principal Technician"),_('Phones'),_('Emails')]
        ]
    for object in objects:
        principaltechnician=""
        phones=""
        emails=""
        for ptechnician in object.principaltechnician_set.all():
            if principaltechnician != "" :
                principaltechnician+=" \n"
                phones+=" \n"
                emails+=" \n"
            principaltechnician += ptechnician.name
            phones += ptechnician.phone_number
            emails += ptechnician.email    
        dev.append([
            object.name,
            object.phone_number,
            object.location,
            principaltechnician,
            phones,
            emails,
            ])
    return dev
    
    
@login_required
@user_lab_perms(perm="report")
def report_organization_building(request, *args, **kwargs):
    var = request.GET.get('organization')
    if var: # when have user selecting org
        org=get_object_or_404(OrganizationStructure, pk=var)
        organizations_child = OrganizationStructure.os_manager.filter_user(request.user)
        if org in organizations_child: # user have perm on that organization ?
                organizations_child = org.get_descendants(include_self=True)
                labs=Laboratory.objects.filter(organization__in=organizations_child)
        else:
            if request.user.is_superuser:
                organizations_child = OrganizationStructure.os_manager.get_children(var)
                labs=Laboratory.objects.filter(organization__in=organizations_child)
            else:        
                labs = Laboratory.objects.none()
    else: # when haven't user selecting org
        organizations_child  = OrganizationStructure.os_manager.filter_user(request.user)
                  
        if organizations_child :   
            labs=Laboratory.objects.filter(organization__in=organizations_child )
        else:
             if request.user.is_superuser:
                labs= Laboratory.objects.all()    
             else:
                labs = Laboratory.objects.none()         
            
    
    fileformat = request.GET.get('format', 'pdf')
    if fileformat in ['xls', 'xlsx', 'ods']:
        return django_excel.make_response_from_array(
        make_book_organization_laboratory(labs), fileformat ,file_name="Laboratories.%s"%(fileformat,))

    
    context = {
        'object_list': labs,
        'datetime': timezone.now(),
        'request': request,
        'laboratory': kwargs.get('lab_pk')
    }

    template = get_template('pdf/organizationlaboratory_pdf.html')

    html = template.render(
        context=context).encode("UTF-8")

    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')
    response[
        'Content-Disposition'] = 'attachment; filename="report_organization_libraries.pdf"'
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
                imdg = ""
                if obj.object.imdg_code is not None:
                    imdg = obj.object.get_imdg_code_display()
                labobj.append([
                    furniture.name,
                    obj.shelf.name,
                    obj.object.code,
                    obj.object.name,
                    obj.quantity,
                    obj.get_measurement_unit_display(),
                    obj.object.get_type_display(),
                    obj.object.cas_id_number or "",
                    imdg
                ])
        if labobj:
            content[labroom.name] = labobj

    return content


@login_required
@user_lab_perms(perm="report")
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

    template = get_template('pdf/laboratoryroom_pdf.html')

    context = {
        'object_list': rooms,
        'datetime': timezone.now(),
        'request': request,
        'laboratory': kwargs.get('lab_pk')
    }

    html = template.render(context=context).encode("UTF-8")

    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')
    response[
        'Content-Disposition'] = 'attachment; filename="report_laboratory.pdf"'
    return response


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
        'object_list': shelf_objects,
        'datetime': timezone.now(),
        'request': request,
        'laboratory': kwargs.get('lab_pk')
    }

    template = get_template('pdf/shelf_object_pdf.html')

    html = template.render(
        context=context).encode("UTF-8")

    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')
    response[
        'Content-Disposition'] = 'attachment; filename="report_shelf_objects.pdf"'
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


@login_required
@user_lab_perms(perm="report")
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
        'object_list': shelf_objects,
        'datetime': timezone.now(),
        'request': request,
        'laboratory': kwargs.get('lab_pk')
    }

    html = template.render(
        context=context).encode("UTF-8")

    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')
    response[
        'Content-Disposition'] = 'attachment; filename="report_limited_shelf_objects.pdf"'
    return response


def make_book_objects(objects, summary=False, type_id=None):

    description = [
        _("Code"), _("Name"), _("Type"), _(
            "Quantity total"), _('Measurement units')
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
    for object in objects:
        obj_info = [
            object.code,
            object.name,
            object.get_type_display(),
            object.quantity_total,
            ShelfObject.get_units(object.measurement_unit)]
        if type_id == '0':
            obj_info += [
                object.molecular_formula,
                object.cas_id_number,
                object.is_precursor,
                object.get_imdg_code_display()]

        content['objects'].append(obj_info)
        if not summary:
            for shelfobj in object.shelfobject_set.all():
                content['objects'].append(['', shelfobj.shelf.furniture.name,
                                           shelfobj.shelf.name,
                                           shelfobj.quantity,
                                           shelfobj.get_measurement_unit_display()
                                           ])
    return content


@login_required
@user_lab_perms(perm="report")
def report_objects(request, *args, **kwargs):
    var = request.GET.get('pk')
    type_id = None
    if var is None:

        if 'lab_pk' in kwargs:
            filters = Q(
                shelfobject__shelf__furniture__labroom__laboratory__pk=kwargs.get('lab_pk'))

        if 'type_id' in request.GET:
            type_id = request.GET.get('type_id', '')
            if type_id:
                filters = filters & Q(type=type_id)

        if 'lab_pk' in kwargs and 'type_id' in request.GET:
            objects = Object.objects.filter(filters)
        else:
            objects = Object.objects.all()
    else:
        objects = Object.objects.filter(pk=var)

    try:
        detail = bool(int(request.GET.get('details', 0)))
    except:
        detail = False

    fileformat = request.GET.get('format', 'pdf')
    if fileformat in ['xls', 'xlsx', 'ods']:
        return django_excel.make_response_from_book_dict(
            make_book_objects(objects, summary=detail, type_id=type_id), fileformat, file_name="objects.%s" % (fileformat,))

    for obj in objects:
        clentry = CLInventory.objects.filter(
            cas_id_number=obj.cas_id_number).first()
        setattr(obj, 'clinventory_entry', clentry)

    template = get_template('pdf/object_pdf.html')

    context = {
        'object_list': objects,
        'datetime': timezone.now(),
        'request': request,
        'laboratory': kwargs.get('lab_pk')
    }

    html = template.render(
        context=context).encode("UTF-8")

    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')
    response[
        'Content-Disposition'] = 'attachment; filename="report_objects.pdf"'
    return response


@login_required
@user_lab_perms(perm="report")
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

    rpo = rpo.filter(type=Object.REACTIVE, is_precursor=True)

    for obj in rpo:
        clentry = CLInventory.objects.filter(
            cas_id_number=obj.cas_id_number).first()
        setattr(obj, 'clinventory_entry', clentry)

    fileformat = request.GET.get('format', 'pdf')
    if fileformat in ['xls', 'xlsx', 'ods']:
        return django_excel.make_response_from_book_dict(
            make_book_objects(rpo, summary=True, type_id='0'), fileformat, file_name="reactive_precursor.%s" % (fileformat,))

    context = {
        'rpo': rpo,
        'datetime': timezone.now(),
        'request': request,
        'laboratory': lab
    }

    html = template.render(context=context).encode('UTF-8')

    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')
    response[
        'Content-Disposition'] = 'attachment; filename="report_reactive_precursor_objects.pdf"'
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


@login_required
@user_lab_perms(perm="report")
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

    template = get_template('pdf/summaryfurniture_pdf.html')

    context = {
        'object_list': furniture,
        'datetime': timezone.now(),
        'request': request,
        'laboratory': lab
    }

    html = template.render(
        context=context).encode("UTF-8")

    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')
    response[
        'Content-Disposition'] = 'attachment; filename="furniture_report.pdf"'
    return response


@method_decorator(login_required, name='dispatch')
@method_decorator(user_lab_perms(perm="search"), name='dispatch')
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


@method_decorator(login_required, name='dispatch')
@method_decorator(user_lab_perms(perm="report"), name='dispatch')
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


@method_decorator(login_required, name='dispatch')
@method_decorator(user_lab_perms(perm="report"), name='dispatch')
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
                             is_precursor=True)
        if not self.all_labs:
            query = query.filter(
                shelfobject__shelf__furniture__labroom__laboratory=self.lab).distinct()

        for obj in query:
            clentry = CLInventory.objects.filter(
                cas_id_number=obj.cas_id_number).first()
            setattr(obj, 'clinventory_entry', clentry)
        return query
