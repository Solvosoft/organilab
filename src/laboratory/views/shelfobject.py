# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''

import json
from base64 import b64decode

import cairosvg
import base64
from django import forms
from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import FormView
from django_ajax.decorators import ajax
from django_ajax.mixin import AJAXMixin
from djgentelella.forms.forms import CustomForm
from djgentelella.widgets import core
from djgentelella.widgets.selects import AutocompleteSelect

from laboratory import utils
from laboratory.forms import ReservationModalForm, AddObjectForm, SubtractObjectForm, ShelfObjectOptions, \
    ShelfObjectListForm, ValidateShelfForm

from laboratory.models import ShelfObject, Shelf, Object, Laboratory, TranferObject, OrganizationStructure, Furniture
from laboratory.views.djgeneric import CreateView, UpdateView, DeleteView, ListView, DetailView
from ..api.serializers import ShelfObjectSerialize, ShelfObjectLaboratoryViewSerializer
from ..logsustances import log_object_change, log_object_add_change
from ..utils import organilab_logentry
from django.core.exceptions import ValidationError


@login_required
def list_shelfobject_render(request, shelf=0, row=0, col=0, org_pk=None,lab_pk=None):
    if shelf == 0:
        var = request.GET.get('shelf', '0')
    else:
        var = shelf
    if var:
        shelfobject = ShelfObject.objects.filter(object=var)
    else:
        shelfobject = ShelfObject.objects.all()

    context = {
        'object_list': shelfobject,
        'data': Shelf.objects.get(pk=shelf),
        'row': row,
        'col': col,
        'laboratory': lab_pk,
        'org_pk':org_pk
    }
    return render_to_string(
        'laboratory/shelfObject_list.html',context,request)


@method_decorator(permission_required('reservations.add_reservation'), name='dispatch')
class ShelfObjectReservationModal(FormView):
    template_name = 'laboratory/reservation_modal.html'
    form_class = ReservationModalForm
    success_message = "Reservation done successfully"
    success_url = "/"


@login_required
@ajax
def list_shelfobject(request, *args, **kwargs):
    return {
        'inner-fragments': {
            '#shelfobject': list_shelfobject_render(request, org_pk=kwargs['org_pk'],lab_pk=kwargs['lab_pk']),
            '#shelfposition': request.GET.get('shelf', '0'),
            '#shelfposition1': request.GET.get('shelf', '0')

        },
    }


class ShelfObjectForm(CustomForm, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)

        super(ShelfObjectForm, self).__init__(*args, **kwargs)
        initial = kwargs.get('initial')
        shelf = initial['shelf']
        if shelf:
            self.fields['measurement_unit'].initial=shelf.measurement_unit
        self.fields['object'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('objectorgsearch', url_suffix='-detail', url_kwargs={'pk': org_pk},
            attrs={
                'data-dropdownparent': "#object_create",
                'data-s2filter-shelf': '#id_shelf'
            }),
            label=_("Reactive/Material/Equipment"),
            help_text=_("Search by name, code or CAS number")
        )

    def clean_measurement_unit(self):
        unit = self.cleaned_data['measurement_unit']
        quantity = self.cleaned_data['quantity']
        shelf = self.cleaned_data['shelf']
        amount = quantity <= shelf.quantity and (quantity+shelf.get_total_refuse()) <= shelf.quantity
        if shelf.measurement_unit==None:
            return unit
        if shelf.measurement_unit==unit:
            if amount or shelf.quantity==0:
                return unit
            else:
                self.add_error('quantity', _("The quantity is more than the shelf has"))

        else:
            self.add_error('measurement_unit',
                           _("Need add the same measurement unit that the shelf has  %(measurement_unit)s")%{
                            'measurement_unit': shelf.measurement_unit
                        })

        return unit


    class Meta:
        model = ShelfObject
        fields = "__all__"
        exclude =['laboratory_name','course_name','creator', 'in_where_laboratory', 'shelf_object_url', 'shelf_object_qr']
        widgets = {
            'shelf': forms.HiddenInput,
            'quantity': core.TextInput,
            'limit_quantity': core.TextInput,
            'measurement_unit': core.Select,

        }

class ShelfObjectRefuseForm(CustomForm, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)
        super(ShelfObjectRefuseForm, self).__init__(*args, **kwargs)
        initial = kwargs.get('initial')
        shelf = initial['shelf']
        if shelf:
            self.fields['measurement_unit'].initial = shelf.measurement_unit
        self.fields['object'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('objectorgsearch', url_suffix='-detail', url_kwargs={'pk': org_pk}, attrs={
                'data-dropdownparent': "#object_create"
            }),
            label=_("Reactive/Material/Equipment"),
            help_text=_("Search by name, code or CAS number")
        )
        self.fields['marked_as_discard'].initial=True
        self.fields['limit_quantity'].initial=0

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get("quantity")
        shelf = cleaned_data.get("shelf")
        measurement_unit = cleaned_data.get("measurement_unit")

        if shelf.measurement_unit == measurement_unit or not shelf.measurement_unit:
            total = shelf.get_total_refuse()
            new_total =total+quantity
            if shelf.quantity>=new_total or not shelf.quantity:
                return cleaned_data
            else:
                self.add_error('quantity',_("The quantity is much larger than the shelf limit %(limit)s"%{
                    'limit': "%s"%(shelf.quantity,)}))
        else:
            self.add_error('measurement_unit',
                           _("The measurent unit is different of there shelf has %(measurement_unit)s")%{
                               'measurement_unit': shelf.measurement_unit
                           })
        return cleaned_data

    class Meta:
        model = ShelfObject
        fields = ["object","shelf","quantity","measurement_unit","course_name","marked_as_discard",'limit_quantity']
        exclude = ['creator',"laboratory_name"]
        widgets = {
            'shelf': forms.HiddenInput,
            'limit_quantity': forms.HiddenInput,
            'quantity': core.TextInput,
            'measurement_unit': core.Select,
            'course_name': core.TextInput,
            'marked_as_discard': core.HiddenInput
        }


class ShelfObjectFormUpdate(CustomForm, forms.ModelForm):
    col = forms.IntegerField(widget=forms.HiddenInput, required=False)
    row = forms.IntegerField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = ShelfObject
        fields = ['shelf', 'quantity', 'limit_quantity', 'measurement_unit']
        exclude =['creator']
        widgets = {
            'shelf': forms.HiddenInput,
            'quantity': core.TextInput,
            'limit_quantity': core.TextInput,
            'measurement_unit': core.Select
        }

class ShelfObjectRefuseFormUpdate(CustomForm, forms.ModelForm):
    col = forms.IntegerField(widget=forms.HiddenInput, required=False)
    row = forms.IntegerField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = ShelfObject
        fields = ['shelf', 'quantity', 'limit_quantity', 'measurement_unit','course_name']
        exclude = ['laboratory_name']
        widgets = {
            'shelf': forms.HiddenInput,
            'quantity': core.TextInput,
            'limit_quantity': core.TextInput,
            'measurement_unit': core.Select,
            'course_name': core.TextInput
        }


@method_decorator(permission_required('laboratory.add_shelfobject'), name='dispatch')
class ShelfObjectCreate(AJAXMixin, CreateView):
    model = ShelfObject
    form_class = ShelfObjectForm
    success_url = "/"

    def get_success_url(self):
        return reverse_lazy('laboratory:list_shelf', args=(self.org, self.lab, self.shelf.furniture.pk))

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.creator= self.request.user
        self.object.in_where_laboratory_id= self.lab
        self.object.save()
        schema = self.request.scheme + "://"
        domain = schema + self.request.get_host()
        url = domain + reverse('laboratory:rooms_list', kwargs={"org_pk": self.org, "lab_pk": self.lab})
        url = url + "#labroom=%d&furniture=%d&shelf=%d&shelfobject=%d" % \
              (self.object.shelf.furniture.labroom.pk, self.object.shelf.furniture.pk, self.object.shelf.pk, self.object.pk)
        self.object.shelf_object_url = url
        img, file = utils.generate_QR_img_file(url, self.request.user, extension_file=".svg", file_name="qrcode")
        self.object.shelf_object_qr = img
        self.object.save()
        file.close()

        log_object_change(self.request.user, self.lab, self.object, 0, self.object.quantity, '', 0, "Create", create=True)
        utils.organilab_logentry(self.request.user, self.object, ADDITION,  changed_data=form.changed_data, relobj=self.lab)

        return {
            'inner-fragments': {
                "#closemodal": '<script>$("#object_create").modal("hide");</script>'
            },
        }

    def get_form_kwargs(self):
        kwargs = CreateView.get_form_kwargs(self)
        if self.request.method == "POST":
            form = ValidateShelfForm(self.request.POST)
        else:
            form = ValidateShelfForm(self.request.GET)
        if form.is_valid():
            shelf = form.cleaned_data['shelf']
            kwargs['initial']['shelf'] = shelf

        kwargs['org_pk'] = self.org
        return kwargs

    def get_form_class(self):
        if self.request.method == 'GET':
            form = ValidateShelfForm(self.request.GET)
        else:
            form = ValidateShelfForm(self.request.POST)

        if form.is_valid():
            self.shelf = form.cleaned_data['shelf']
            if self.shelf.discard:
                return ShelfObjectRefuseForm
        return self.form_class

    def form_invalid(self, form):
        response = CreateView.form_invalid(self, form)
        response.render()
        return {
            'inner-fragments': {
                '#shelfobjectCreate': response.content
            }
        }

@method_decorator(permission_required('laboratory.change_shelfobject'), name='dispatch')
class ShelfObjectEdit(AJAXMixin, UpdateView):
    model = ShelfObject
    form_class = ShelfObjectFormUpdate
    success_url = "/"

    def get_success_url(self):
        return reverse_lazy('laboratory:list_shelf', args=(self.org, self.lab, self.object.shelf.furniture.pk))

    def form_valid(self, form):
        old = self.model.objects.filter(pk=self.object.id).values('quantity')[0]['quantity']
        self.object = form.save()
        log_object_change(self.request.user, self.lab, self.object, old, self.object.quantity, '', 0,"Edit", create=False)
        utils.organilab_logentry(self.request.user, self.object, CHANGE,  changed_data=form.changed_data, relobj=self.lab)

        row = form.cleaned_data['row']
        col = form.cleaned_data['col']
        return {
            'inner-fragments': {
                '#row_%d_col_%d_shelf_%d' % (row, col, self.object.shelf.pk):
                    list_shelfobject_render(
                        self.request, self.object.shelf.pk, row, col,org_pk=self.org, lab_pk=self.lab),
                "#closemodal": '<script>$("#object_update").modal("hide");</script>'
            },
        }

    def get_form_kwargs(self):
        kwargs = UpdateView.get_form_kwargs(self)

        if self.request.method == "POST":
            form = ValidateShelfForm(self.request.POST)
        else:
            form = ValidateShelfForm(self.request.GET)
        if form.is_valid():
            shelf = form.cleaned_data['shelf']
            kwargs['initial']['shelf'] = shelf
            kwargs['initial']['row'] = form.cleaned_data['row']
            kwargs['initial']['col'] = form.cleaned_data['col']
        return kwargs


@method_decorator(permission_required('laboratory.change_shelfobject'), name='dispatch')
class ShelfObjectSearchUpdate(AJAXMixin, UpdateView):
    model = ShelfObject
    form_class = ShelfObjectFormUpdate
    success_url = "/"

    def get(self, request, *args, **kwargs):
        response = UpdateView.get(self, request, *args, **kwargs)
        response.render()
        return {
            'inner-fragments': {
                '#o%d' % self.object.pk: response.content
            },
        }

    def get_context_data(self, **kwargs):
        context = UpdateView.get_context_data(self, **kwargs)
        context['insearch'] = True
        return context

    def form_valid(self, form):
        self.fvalid = True
        old = self.model.objects.filter(pk=self.object.id).values('quantity')[0]['quantity']
        response = UpdateView.form_valid(self, form)
        log_object_change(self.request.user, self.lab, self.object, old, self.object.quantity, '', 0, "Update",
                          create=False)
        return response

    def post(self, request, *args, **kwargs):
        self.fvalid = False
        response = UpdateView.post(self, request, *args, **kwargs)

        if self.fvalid:
            return {
                'inner-fragments': {
                    '#o%d' % self.object.pk: render_to_string(
                        'laboratory/shelfObject.html',
                        {'object': self.object,
                         'laboratory': self.lab},request)
                },
            }
        response.render()
        return {
            'inner-fragments': {
                '#o%d' % self.object.pk: response.content
            },
        }


@method_decorator(permission_required('laboratory.delete_shelfobject'), name='dispatch')
class ShelfObjectDelete(AJAXMixin, DeleteView):
    model = ShelfObject
    success_url = "/"

    def form_valid(self, form):
        utils.organilab_logentry(self.request.user, self.object, DELETION, relobj=self.lab)
        self.object.delete()
        data = {
            'inner-fragments': {
                "#closemodal": '<script>$("#object_delete").modal("hide");</script>'
            }
        }
        return data

@method_decorator(permission_required('laboratory.view_shelfobject'), name='dispatch')
class ShelfObjectDetail(AJAXMixin, DetailView):
    model = ShelfObject


@permission_required('laboratory.change_shelfobject')
def add_object(request, org_pk, lab_pk, pk):
    """ The options represents several actions in numbers 1=Reservation, 2=Add, 3=Tranfer, 4=Subtract"""
    elements_form=ShelfObjectOptions(request.POST)
    response={}
    if elements_form.is_valid():
        action = elements_form.cleaned_data['options']
        lab = elements_form.cleaned_data['lab']
        form = AddObjectForm(request.POST, lab=lab.pk)
        org = lab.organization
        shelfobject = ShelfObject.objects.filter(pk=elements_form.cleaned_data['shelf_object']).first()

        if action == 2:
            if form.is_valid():

                amount = form.cleaned_data['amount']

                old = shelfobject.quantity
                new = old + amount
                shelfobject.quantity = new

                shelf = shelfobject.shelf
                if shelf.discard:
                    total = shelf.get_total_refuse()
                    new_total = total+amount
                    if shelf.quantity>=new_total or not shelf.quantity:
                        shelfobject.save()
                        log_object_add_change(request.user, pk, shelfobject, old, new, "Add", form.cleaned_data['provider'],
                                              form.cleaned_data['bill'], create=False)
                        organilab_logentry(request.user, shelfobject, CHANGE, 'shelfobject', changed_data=form.changed_data)

                        response = {
                            'status': True,
                            'msg': _('Added successfully'),
                            'object': {'object':shelfobject.__str__(),
                                       'amount': shelfobject.quantity,
                                       'unit': shelfobject.measurement_unit.description,
                                       'pk': shelf.pk}
                        }
                        return JsonResponse(response)
                    else:
                        return JsonResponse({'status': False, 'msg': _('The quantity is much larger than the shelf limit %(limit)s') %{
                            'limit': "%s"%(shelf.quantity)
                        } })

                else:
                    status=False
                    if shelf.measurement_unit==None:
                        status=True
                    if shelf.measurement_unit==shelfobject.measurement_unit:
                        quantity = (amount+shelf.get_total_refuse()) <= shelf.quantity
                        if quantity:
                            status=True
                    if shelf.measurement_unit==shelfobject.measurement_unit and shelf.quantity==0:
                        status=True

                    if status:
                        shelfobject.save()
                        log_object_add_change(request.user, pk, shelfobject, old, new, "Add", request.POST.get('provider'),
                                              request.POST.get('bill'), create=False)
                        organilab_logentry(request.user, shelfobject, CHANGE, 'shelfobject', changed_data=form.changed_data)
                        response = {
                            'status': True,
                            'msg': _('Added successfully'),
                            'object': {'object': shelfobject.__str__(),
                                       'amount': shelfobject.quantity,
                                       'pk': shelf.pk,
                                       'unit': shelfobject.measurement_unit.description}
                        }
                    else:
                        response = {
                            'status': False,
                            'msg': _('The quantity is more than the shelf has'),
                            'object': {'object': shelfobject.__str__(),
                                       'amount': shelfobject.quantity,
                                       'pk': shelf.pk,
                                       'unit': shelfobject.measurement_unit.description}
                        }

                    return JsonResponse(response)

            else:
                return JsonResponse({'status': False,'msg':_('Complete the fields')})
        elif action == 4:
            return subtract_object(request, pk, elements_form)
        else:
            return transfer_object(request, pk, org_pk, elements_form)
    return JsonResponse({'status': True, 'msg': _('Added successfully')})

add_object.lab_pk_field= 'pk'

def get_shelfobject_template(request,lab,org,shelfobject):
    return render_to_string(template_name="laboratory/components/shelfobject.html",
                                context={'shelfobject': shelfobject, 'laboratory': lab,
                                         'org_pk': org},
                                request=request)
@permission_required('laboratory.change_shelfobject')
def subtract_object(request, pk, elements_form):
    shelfobject = ShelfObject.objects.filter(pk=elements_form.cleaned_data['shelf_object']).first()
    old = shelfobject.quantity
    form = SubtractObjectForm(request.POST)


    if form.is_valid():
        try:
            amount = float(form.cleaned_data['discount'])
        except ValueError:
            return JsonResponse({'msg': False})
        if old >= amount:
            new = old - amount
            shelfobject.quantity = new
            shelfobject.save()
            log_object_change(request.user, pk, shelfobject, old, new, form.cleaned_data['description'], 2, "Substract", create=False)
            utils.organilab_logentry(request.user, shelfobject, CHANGE, 'shelfobject', changed_data=form.changed_data)
            template = render_to_string(template_name="laboratory/components/shelfobject.html",
                                        context={'shelfobject': shelfobject,
                                                 'laboratory': elements_form.cleaned_data['lab'].pk,
                                                 'org_pk': elements_form.cleaned_data['lab'].organization.pk},
                                        request=request)


        else:
            template = render_to_string(template_name="laboratory/components/shelfobject.html",
                                        context={'shelfobject': shelfobject,
                                                 'laboratory': elements_form.cleaned_data['lab'].pk,
                                                 'org_pk': elements_form.cleaned_data['lab'].organization.pk},
                                        request=request)
            response = {
                'template':template,
                'status': False,
                'msg': _('The amount to be subtracted is more than the shelf has'),
                'object': {'object': shelfobject.__str__(),
                           'amount': shelfobject.quantity,
                           'unit': shelfobject.measurement_unit.description}

            }

            return JsonResponse(response)
    else:
        template = render_to_string(template_name="laboratory/components/shelfobject.html",
                                    context={'shelfobject': shelfobject,
                                             'laboratory': elements_form.cleaned_data['lab'].pk,
                                             'org_pk': elements_form.cleaned_data['lab'].organization.pk},
                                    request=request)
        return JsonResponse({'status': False, 'template':template, 'msg': _('Complete the fields')})
    template = render_to_string(template_name="laboratory/components/shelfobject.html",
                                context={'shelfobject': shelfobject, 'laboratory': elements_form.cleaned_data['lab'].pk,
                                         'org_pk': elements_form.cleaned_data['lab'].organization.pk},
                                request=request)
    response = {

        'template':template,
        'status': True,
        'msg': _('Sustracted successfully'),
        'object': {'object': shelfobject.__str__(),
                   'amount': shelfobject.quantity,
                   'unit': shelfobject.measurement_unit.description}
    }
    return JsonResponse(response)


@permission_required('laboratory.add_tranferobject')
def transfer_object(request, pk, org_pk, elements_form):

    try:
        amount = float(request.POST.get('amount_send'))
    except ValueError:
        return JsonResponse({'status': False, 'msg': _('Only can accept whole numbers or decimal numbers with .')})
    obj = ShelfObject.objects.filter(pk=elements_form.cleaned_data['shelf_object']).first()
    template = render_to_string(template_name="laboratory/components/shelfobject.html",
                                context={'shelfobject': obj, 'laboratory': elements_form.cleaned_data['lab'].pk,
                                         'org_pk': elements_form.cleaned_data['lab'].organization.pk},
                                request=request)
    if amount <= obj.quantity:
        lab_send = Laboratory.objects.filter(pk=pk).first()
        lab_received = Laboratory.objects.filter(pk=request.POST.get('laboratory')).first()
        mark_as_discard = request.POST.get('mark_as_discard', '')
        transfer = TranferObject.objects.create(object=obj,
                                     laboratory_send=lab_send,
                                     laboratory_received=lab_received,
                                     quantity=amount,
                                     mark_as_discard= mark_as_discard.lower() in ['on', 'true', '1']
                                     )
        changed_data = ['object', 'laboratory_send', 'laboratory_received', 'quantity']
        utils.organilab_logentry(request.user, transfer, ADDITION,  changed_data=changed_data, relobj=[lab_send, transfer])
    else:
        return JsonResponse({'status': False,'template':template,'msg': _('The amount sending is less that the amount we have in the Shelf')})

    view=Object()
    setattr(view, 'data', {'laboratory': pk, 'organization': org_pk})
    serializer=ShelfObjectLaboratoryViewSerializer(instance=obj, context={'view': view, 'request': request})
    return JsonResponse({'status': True, 'template': template, "object": serializer.data, 'msg': _('Transfer done successfully')})


@csrf_exempt
def send_detail(request, *args, **kwargs):
    obj = ShelfObject.objects.get(pk=request.POST.get('shelf_object'))
    return JsonResponse({'obj': obj.get_object_detail()})

@method_decorator(permission_required('laboratory.view_tranferobject'), name='dispatch')
class ListTransferObjects(ListView):
    model = TranferObject
    template_name = 'laboratory/transfer_objects.html'

    def get_queryset(self):
        return TranferObject.objects.filter(Q(laboratory_send__id=self.request.GET.get('lab')) |
                                            Q(laboratory_received__id=self.request.GET.get('lab'))).order_by(
            'pk').reverse()

@login_required()
def get_shelf_list(request):
    form = ShelfObjectListForm(request.POST)
    data = None
    aux = []
    unit = None
    msg= None

    if form.is_valid():
        lab = form.cleaned_data['lab'].pk
        furnitures = Furniture.objects.filter(labroom__laboratory__id=lab)

        transfer_detail = TranferObject.objects.filter(pk=form.cleaned_data['id']).first()

        if furnitures and transfer_detail:
            msg = transfer_detail.get_object_detail()
            unit = transfer_detail.object.measurement_unit

            for furniture in furnitures:
                replacements = [('[', ''), (']', '')]
                dataconfig = furniture.dataconfig

                for simbol,config in replacements:

                    if simbol in dataconfig:
                        dataconfig = dataconfig.replace(simbol,"")

                data = [x for x in dataconfig.split(',') if x != '']
                if len(data)>0:
                    for shelf in Shelf.objects.filter(pk__in=data):
                        if unit == shelf.measurement_unit or shelf.measurement_unit==None:
                            aux.append({'id': shelf.pk, 'shelf': shelf.get_shelf()})
        else:
            msg=form.errors
    data = json.dumps(aux)
    return JsonResponse({'data': data, 'msg': msg})


@permission_required('laboratory.add_tranferobject')
def objects_transfer(request, org_pk, lab_pk, transfer_pk, shelf_pk):
    transfer = get_object_or_404(TranferObject, pk=transfer_pk)
    shelf = get_object_or_404(Shelf, pk=shelf_pk)
    obj = transfer.object.object
    lab_send_obj = ShelfObject.objects.get(pk=transfer.object.pk)

    if lab_send_obj.quantity >= transfer.quantity:
        lab_received_obj = ShelfObject.objects.filter(object_id=obj.id, shelf_id=shelf_pk).first()

        if lab_received_obj is not None:
             old = lab_received_obj.quantity
             lab_received_obj.quantity += transfer.quantity
             if transfer.mark_as_discard:
                 lab_received_obj.marked_as_discard = True
             lab_received_obj.in_where_laboratory_id = lab_pk
             lab_received_obj.save()

             log_object_change(request.user, transfer.laboratory_received.pk, lab_received_obj, old,
                                  lab_received_obj.quantity,
                                  'Transferencia de %s por parte del laboratorio %s'% (transfer.get_object_detail(), transfer.laboratory_send.name),
                    1,"Transfer", create=False)

        else:
            new_object = ShelfObject.objects.create(shelf=shelf,
                                           object=obj,
                                           quantity=transfer.quantity,
                                           limit_quantity=0,
                                           in_where_laboratory_id=lab_pk,
                                           measurement_unit=lab_send_obj.measurement_unit)

            schema = request.scheme + "://"
            domain = schema + request.get_host()
            url = domain + reverse('laboratory:rooms_list', kwargs={"org_pk": org_pk, "lab_pk": lab_pk})
            url = url + "#labroom=%d&furniture=%d&shelf=%d&shelfobject=%d" % \
                  (shelf.furniture.labroom.pk, shelf.furniture.pk, shelf.pk, new_object.pk)
            new_object.shelf_object_url = url
            img, file = utils.generate_QR_img_file(url, request.user, extension_file=".svg", file_name="qrcode")
            new_object.shelf_object_qr = img

            if transfer.mark_as_discard:
                new_object.marked_as_discard = True
            new_object.save()
            log_object_change(request.user, transfer.laboratory_received.pk, lab_send_obj, 0,
                              transfer.quantity,
                              'Transferencia de %s por parte del laboratorio %s' % (
                              transfer.get_object_detail(), transfer.laboratory_send.name),
                              1, "Transfer", create=False)

            changed_data = ['shelf', 'object', 'quantity', 'limit_quantity', 'measurement_unit']
            utils.organilab_logentry(request.user, new_object, ADDITION,  changed_data=changed_data,
                               relobj=[transfer.laboratory_received, transfer.laboratory_send])

        old = lab_send_obj.quantity
        lab_send_obj.quantity -= transfer.quantity
        lab_send_obj.save()
        transfer.status = 1
        transfer.save()
        log_object_change(request.user, transfer.laboratory_send.pk, lab_send_obj, old, lab_send_obj.quantity,
                    'Transferencia de %s al laboratorio %s'% (transfer.get_object_detail(), transfer.laboratory_received.name),
                          2, "Transfer", create=False)
        messages.success(request, _("Transfer done successfully"))
    else:
        return JsonResponse({'status': False, 'msg': _('The amount sends is more than the laboratory have')})
    return JsonResponse({'status': True, 'msg': _('Transfer done successfully')})


objects_transfer.lab_pk_field = 'lab_pk'

@permission_required('laboratory.delete_tranferobject')
def delete_transfer(request, pk):
    try:
        transfer = TranferObject.objects.get(pk=int(request.POST.get('id')))
        transfer.delete()
        utils.organilab_logentry(request.user, transfer, DELETION, relobj=[transfer.laboratory_send, transfer.laboratory_received ])
    except TranferObject.DoesNotExist:
        return JsonResponse({'data': False})
    return JsonResponse({'data': True})


delete_transfer.lab_pk_field = 'pk'

@login_required()
@permission_required('laboratory.change_shelfobject')
def edit_limit_object(request, *args, **kwargs):
    shelf_object = ShelfObject.objects.filter(pk=kwargs['pk']).first()
    context ={
        'name':shelf_object.object.name,
        'msg':'',
        'amount': shelf_object.limit_quantity
    }
    if request.method=='POST':
        shelf_object.limit_quantity=float(request.POST.get('amount'))
        shelf_object.save()
        context['msg'] ='Se guardo correctamente'
        context['amount'] ='Se guardo correctamente'
        return JsonResponse(context)
    context ={
        'name':shelf_object.object.name,
        'msg':'',
        'amount': shelf_object.limit_quantity
    }
    return JsonResponse(context)


@login_required
@permission_required('laboratory.view_shelfobject')
def download_shelfobject_qr(request, org_pk, lab_pk, pk):
    shelfobject = get_object_or_404(ShelfObject, pk=pk)
    try:
        file = shelfobject.shelf_object_qr
        response = HttpResponse(file, content_type='image/svg')
    except IOError:
        return HttpResponseNotFound()
    response['Content-Disposition'] = 'attachment; filename="shelfobject_%s.svg"' % (shelfobject.pk)
    return response