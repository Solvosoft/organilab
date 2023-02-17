# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''

import json

from django import forms
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect
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

from laboratory.decorators import has_lab_assigned
from laboratory.forms import ReservationModalForm, AddObjectForm, SubtractObjectForm
from laboratory.models import ShelfObject, Shelf, Object, Laboratory, TranferObject, OrganizationStructure
from laboratory.views.djgeneric import CreateView, UpdateView, DeleteView, ListView, DetailView
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
    col = forms.IntegerField(widget=forms.HiddenInput)
    row = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)
        super(ShelfObjectForm, self).__init__(*args, **kwargs)

        self.fields['object'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('objectorgsearch', url_suffix='-detail', url_kwargs={'pk': org_pk}, attrs={
                'data-dropdownparent': "#object_create"
            }),
            label=_("Reactive/Material/Equipment"),
            help_text=_("Search by name, code or CAS number")
        )

    class Meta:
        model = ShelfObject
        fields = "__all__"
        exclude =['laboratory_name','course_name']
        widgets = {
            'shelf': forms.HiddenInput,
            'quantity': core.TextInput,
            'limit_quantity': core.TextInput,
            'measurement_unit': core.Select,

        }
class ShelfObjectRefuseForm(CustomForm, forms.ModelForm):
    col = forms.IntegerField(widget=forms.HiddenInput)
    row = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)
        super(ShelfObjectRefuseForm, self).__init__(*args, **kwargs)

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
        if shelf.measurement_unit == measurement_unit:
            total = shelf.get_total_refuse()
            new_total =total+quantity
            if shelf.quantity>=new_total:
                return cleaned_data
            else:
                raise ValidationError(_("The quantity is much larger than the shelf limit"))
        else:
            raise ValidationError(_("The measurent unit is different of there shelf has"))

    class Meta:
        model = ShelfObject
        fields = ["object","shelf","quantity","measurement_unit","laboratory_name","course_name","marked_as_discard",'limit_quantity']
        widgets = {
            'shelf': forms.HiddenInput,
            'limit_quantity': forms.HiddenInput,
            'quantity': core.TextInput,
            'measurement_unit': core.Select,
            'laboratory_name': core.TextInput,
            'course_name': core.TextInput,
            'marked_as_discard': core.HiddenInput
        }


class ShelfObjectFormUpdate(CustomForm, forms.ModelForm):
    col = forms.IntegerField(widget=forms.HiddenInput, required=False)
    row = forms.IntegerField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = ShelfObject
        fields = ['shelf', 'quantity', 'limit_quantity', 'measurement_unit']
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
        fields = ['shelf', 'quantity', 'limit_quantity', 'measurement_unit','laboratory_name','course_name']
        widgets = {
            'shelf': forms.HiddenInput,
            'quantity': core.TextInput,
            'limit_quantity': core.TextInput,
            'measurement_unit': core.Select,
            'laboratory_name': core.TextInput,
            'course_name': core.TextInput
        }


@method_decorator(has_lab_assigned(), name="dispatch")
@method_decorator(permission_required('laboratory.add_shelfobject'), name='dispatch')
class ShelfObjectCreate(AJAXMixin, CreateView):
    model = ShelfObject
    form_class = ShelfObjectForm
    success_url = "/"

    def get_success_url(self):
        return reverse_lazy('laboratory:list_shelf', args=(self.org, self.lab))

    def form_valid(self, form):
        self.object = form.save()
        log_object_change(self.request.user, self.lab, self.object, 0, self.object.quantity, '', 0, "Create", create=True)
        organilab_logentry(self.request.user, self.object, ADDITION,  changed_data=form.changed_data, relobj=self.lab)

        row = form.cleaned_data['row']
        col = form.cleaned_data['col']
        return {
            'inner-fragments': {
                '#row_%d_col_%d_shelf_%d' % (row, col, self.object.shelf.pk): list_shelfobject_render(
                    self.request, self.object.shelf.pk, row, col, org_pk=self.org, lab_pk=self.lab),
                "#closemodal": '<script>$("#object_create").modal("hide");</script>'
            },
        }

    def get_form_kwargs(self):
        kwargs = CreateView.get_form_kwargs(self)
        shelf=self.request.GET.get('shelf')
        kwargs['initial']['shelf'] = shelf
        kwargs['initial']['row'] = self.request.GET.get('row')
        kwargs['initial']['col'] = self.request.GET.get('col')
        kwargs['org_pk'] = self.org
        return kwargs

    def get_form_class(self):
        shelf=None
        if self.request.method == 'GET' and 'shelf' in self.request.GET:
            shelf = get_object_or_404(Shelf,pk=int(self.request.GET['shelf']))
        else:
            shelf = get_object_or_404(Shelf,pk=int(self.request.POST['shelf']))

        if shelf.discard:
            return ShelfObjectRefuseForm
        return self.form_class
    def form_invalid(self, form):
        msg = form.errors["__all__"][0]
        return {
            'inner-fragments': {
                '#msg': msg
            },
        }

@method_decorator(has_lab_assigned(), name="dispatch")
@method_decorator(permission_required('laboratory.change_shelfobject'), name='dispatch')
class ShelfObjectEdit(AJAXMixin, UpdateView):
    model = ShelfObject
    form_class = ShelfObjectFormUpdate
    success_url = "/"

    def get_success_url(self):
        return reverse_lazy('laboratory:list_shelf', args=(self.org, self.lab))

    def form_valid(self, form):
        old = self.model.objects.filter(pk=self.object.id).values('quantity')[0]['quantity']
        self.object = form.save()
        log_object_change(self.request.user, self.lab, self.object, old, self.object.quantity, '', 0,"Edit", create=False)
        organilab_logentry(self.request.user, self.object, CHANGE,  changed_data=form.changed_data, relobj=self.lab)

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
        kwargs['initial']['shelf'] = self.request.GET.get('shelf')
        kwargs['initial']['row'] = self.request.GET.get('row')
        kwargs['initial']['col'] = self.request.GET.get('col')
        return kwargs


@method_decorator(has_lab_assigned(), name="dispatch")
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


@method_decorator(has_lab_assigned(), name="dispatch")
@method_decorator(permission_required('laboratory.delete_shelfobject'), name='dispatch')
class ShelfObjectDelete(AJAXMixin, DeleteView):
    model = ShelfObject
    success_url = "/"

    def get_success_url(self):
        return reverse_lazy('laboratory:list_shelf', args=(self.org, self.lab))

    def get_context_data(self, **kwargs):
        context = DeleteView.get_context_data(self, **kwargs)
        context['row'] = self.row
        context['col'] = self.col
        return context

    def get(self, request, *args, **kwargs):
        self.row = request.GET.get("row")
        self.col = request.GET.get("col")
        return DeleteView.get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        DeleteView.post(self, request, *args, **kwargs)
        self.row = request.POST.get("row")
        self.col = request.POST.get("col")

        return {
            'inner-fragments': {
                '#row_%s_col_%s_shelf_%d' % (self.row, self.col, self.object.shelf.pk): list_shelfobject_render(
                    request, row=self.row, col=self.col, shelf=self.object.shelf.pk, org_pk=self.org, lab_pk=self.lab),
                "#closemodal": '<script>$("#object_delete").modal("hide");</script>'
            },
        }

    def form_valid(self, form):
        success_url = self.get_success_url()
        organilab_logentry(self.request.user, self.object, DELETION, relobj=self.lab)
        self.object.delete()
        return HttpResponseRedirect(success_url)



@method_decorator(permission_required('laboratory.view_shelfobject'), name='dispatch')
class ShelfObjectDetail(AJAXMixin, DetailView):
    model = ShelfObject


@permission_required('laboratory.change_shelfobject')
def add_object(request, pk):
    """ The options represents several actions in numbers 1=Reservation, 2=Add, 3=Tranfer, 4=Subtract"""
    action = int(request.POST.get('options'))
    form = AddObjectForm(request.POST, lab=request.POST.get('lab'))

    if action == 2:
        if form.is_valid():
            try:
                amount = float(request.POST.get('amount'))
            except ValueError:
                return JsonResponse({'msg': False})
            object = ShelfObject.objects.filter(pk=request.POST.get('shelf_object')).first()
            old = object.quantity
            new = old + amount
            object.quantity = new
            shelf = object.shelf
            if shelf.discard:
                total = shelf.get_total_refuse()
                new_total = total+amount
                if shelf.quantity>=new_total:

                    object.save()
                    log_object_add_change(request.user, pk, object, old, new, "Add", request.POST.get('provider'),
                                          request.POST.get('bill'), create=False)
                    organilab_logentry(request.user, object, CHANGE, 'shelfobject', changed_data=form.changed_data)

                    response = {
                        'status': True,
                        'msg': _('Added successfully'),
                        'object': {'object':object.__str__(),
                                   'amount': object.quantity,
                                   'unit':object.measurement_unit.description}
                    }
                    return JsonResponse(response)
                else:
                    return JsonResponse({'status': False, 'msg': _('The quantity is much larger than the shelf limit')})

            else:
                object.save()
                log_object_add_change(request.user, pk, object, old, new, "Add", request.POST.get('provider'),
                                      request.POST.get('bill'), create=False)
                organilab_logentry(request.user, object, CHANGE, 'shelfobject', changed_data=form.changed_data)

                response = {
                    'status': True,
                    'msg': _('Added successfully'),
                    'object': {'object': object.__str__(),
                               'amount': object.quantity,
                               'unit': object.measurement_unit.description}
                }
                return JsonResponse(response)

        else:
            return JsonResponse({'status': False,'msg':_('Complete the fields')})
    elif action == 4:
        return subtract_object(request, pk)
    else:
        return transfer_object(request, pk)
    return JsonResponse({'status': True, 'msg': _('Added successfully')})

add_object.lab_pk_field= 'pk'

@permission_required('laboratory.change_shelfobject')
def subtract_object(request, pk):
    object = ShelfObject.objects.filter(pk=request.POST.get('shelf_object')).first()
    old = object.quantity
    form = SubtractObjectForm(request.POST)
    if form.is_valid():
        try:
            amount = float(form.cleaned_data['discount'])
        except ValueError:
            return JsonResponse({'msg': False})
        if old >= amount:
            new = old - amount
            object.quantity = new
            object.save()
            log_object_change(request.user, pk, object, old, new, form.cleaned_data['description'], 2, "Substract", create=False)
            organilab_logentry(request.user, object, CHANGE, 'shelfobject', changed_data=form.changed_data)

        else:
            response = {
                'status': False,
                'msg': _('The amount to be subtracted is more than the shelf has'),
                'object': {'object': object.__str__(),
                           'amount': object.quantity,
                           'unit': object.measurement_unit.description}

            }

            return JsonResponse(response)
    else:
        return JsonResponse({'status': False, 'msg': _('Complete the fields')})
    response = {
        'status': True,
        'msg': _('Sustracted successfully'),
        'object': {'object': object.__str__(),
                   'amount': object.quantity,
                   'unit': object.measurement_unit.description}
    }
    return JsonResponse(response)


@permission_required('laboratory.add_tranferobject')
def transfer_object(request, pk):
    try:
        amount = float(request.POST.get('amount_send'))
    except ValueError:
        return JsonResponse({'status': False, 'msg': _('Only can accept whole numbers or decimal numbers with .')})
    obj = ShelfObject.objects.filter(pk=request.POST.get('shelf_object')).first()
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
        organilab_logentry(request.user, transfer, ADDITION,  changed_data=changed_data, relobj=[lab_send, transfer])
    else:
        return JsonResponse({'status': False, 'msg': _('The amount sending is less that the amount we have in the Shelf')})
    return JsonResponse({'status': True, 'msg': _('Transfer done successfully')})


@csrf_exempt
def send_detail(request):
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
    shelfs = Shelf.objects.filter(furniture__labroom__laboratory__id=int(request.POST.get('lab')))
    transfer_detail = TranferObject.objects.filter(pk=int(request.POST.get('id'))).first()
    aux = []
    for shelf in shelfs:
        aux.append({'id': shelf.pk, 'shelf': shelf.get_shelf()})
    data = json.dumps(aux)
    return JsonResponse({'data': data, 'msg': transfer_detail.get_object_detail()})


@permission_required('laboratory.add_tranferobject')
def objects_transfer(request,pk):
    data = TranferObject.objects.get(pk=int(request.POST.get('transfer_id')))
    obj = data.object.object
    lab_send_obj = ShelfObject.objects.get(pk=data.object.pk)

    try:
        shelf = int(request.POST.get('shelf'))
    except ValueError:
        return JsonResponse({'status': False, 'msg': _('Need to create a Shelf')})

    if lab_send_obj.quantity >= data.quantity:
        lab_received_obj = ShelfObject.objects.filter(object_id=obj.id, shelf_id=shelf).first()

        if lab_received_obj is not None:
             old = lab_received_obj.quantity
             lab_received_obj.quantity += data.quantity
             if data.mark_as_discard:
                 lab_received_obj.marked_as_discard = True
             lab_received_obj.save()

             log_object_change(request.user, data.laboratory_received.pk, lab_received_obj, old,
                                  lab_received_obj.quantity,
                                  'Transferencia de %s por parte del laboratorio %s'% (data.get_object_detail(), data.laboratory_send.name),
                    1,"Transfer", create=False)

        else:
            get_shelf = Shelf.objects.get(pk=shelf)
            new_object = ShelfObject.objects.create(shelf=get_shelf,
                                           object=obj,
                                           quantity=data.quantity,
                                           limit_quantity=0,
                                           measurement_unit=lab_send_obj.measurement_unit)
            if data.mark_as_discard:
                new_object.marked_as_discard = True
            new_object.save()
            log_object_change(request.user, data.laboratory_received.pk, lab_send_obj, 0,
                              data.quantity,
                              'Transferencia de %s por parte del laboratorio %s' % (
                              data.get_object_detail(), data.laboratory_send.name),
                              1, "Transfer", create=False)

            changed_data = ['shelf', 'object', 'quantity', 'limit_quantity', 'measurement_unit']
            organilab_logentry(request.user, new_object, ADDITION,  changed_data=changed_data,
                               relobj=[data.laboratory_received, data.laboratory_send])

        old = lab_send_obj.quantity
        lab_send_obj.quantity -= data.quantity
        lab_send_obj.save()
        data.status = 1
        data.save()
        log_object_change(request.user, data.laboratory_send.pk, lab_send_obj, old, lab_send_obj.quantity,
                    'Transferencia de %s al laboratorio %s'% (data.get_object_detail(), data.laboratory_received.name),
                          2, "Transfer", create=False)
    else:
        return JsonResponse({'status': False, 'msg': _('The amount sends is more than the laboratory have')})
    return JsonResponse({'status': True, 'msg': _('Transfer done successfully')})


objects_transfer.lab_pk_field = 'pk'

@permission_required('laboratory.delete_tranferobject')
def delete_transfer(request,pk):
    try:
        transfer = TranferObject.objects.get(pk=int(request.POST.get('id')))
        transfer.delete()
        organilab_logentry(request.user, transfer, DELETION, relobj=[transfer.laboratory_send, transfer.laboratory_received ])
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