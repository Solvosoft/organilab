# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''

from django import forms
from django.contrib.auth.decorators import login_required, permission_required
from django.template.loader import render_to_string
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator
from django_ajax.decorators import ajax
from django_ajax.mixin import AJAXMixin
from djgentelella.forms.forms import CustomForm
from djgentelella.widgets import core
from laboratory.models import ShelfObject, Shelf, Object,Laboratory,TranferObject
from .djgeneric import CreateView, UpdateView, DeleteView,ListView
from django.utils.translation import ugettext_lazy as _
from djgentelella.widgets.selects import AutocompleteSelect
from ..logsustances import log_object_change,log_object_add_change
from django.views.generic.edit import FormView
from laboratory.forms import ReservationModalForm,AddObjectForm,TransferObjectForm,SubtractObjectForm,AddTransferObjectForm
from laboratory.decorators import has_lab_assigned
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import json


@login_required
def list_shelfobject_render(request, shelf=0, row=0, col=0, lab_pk=None):
    if shelf == 0:
        var = request.GET.get('shelf', '0')
    else:
        var = shelf
    if var:
        shelfobject = ShelfObject.objects.filter(object=var)
    else:
        shelfobject = ShelfObject.objects.all()
    return render_to_string(
        'laboratory/shelfObject_list.html',
        context={
            'object_list': shelfobject,
            'data': Shelf.objects.get(pk=shelf),
            'row': row,
            'col': col,
            'laboratory': lab_pk,
            'request': request
        })


@method_decorator(permission_required('reservations.add_reservation'), name='dispatch')
class ShelfObjectReservationModal(FormView):
    template_name = 'laboratory/reservation_modal.html'
    form_class = ReservationModalForm
    success_message = "Reservation done successfully"
    success_url = "/"



@login_required
@ajax
def list_shelfobject(request, lab_pk):
    return {
        'inner-fragments': {
            '#shelfobject': list_shelfobject_render(request, lab_pk=lab_pk),
            '#shelfposition': request.GET.get('shelf', '0'),
            '#shelfposition1': request.GET.get('shelf', '0')

        },
    }


class ShelfObjectForm(CustomForm, forms.ModelForm):
    col = forms.IntegerField(widget=forms.HiddenInput)
    row = forms.IntegerField(widget=forms.HiddenInput)
    object = forms.ModelChoiceField(
        queryset=Object.objects.all(),
        widget=AutocompleteSelect('objectsearch'),
        label=_("Reactive/Material/Equipment"),
        help_text=_("Search by name, code or CAS number")
    )

    class Meta:
        model = ShelfObject
        fields = "__all__"
        widgets = {
            'shelf': forms.HiddenInput,
            'quantity': core.TextInput,
            'limit_quantity': core.TextInput,
            'measurement_unit': core.Select
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


@method_decorator(has_lab_assigned(), name="dispatch")
@method_decorator(permission_required('laboratory.add_shelfobject'), name='dispatch')
class ShelfObjectCreate(AJAXMixin, CreateView):
    model = ShelfObject
    form_class = ShelfObjectForm
    success_url = "/"

    def get_success_url(self):
        return reverse_lazy('laboratory:list_shelf', args=(self.lab,))

    def form_valid(self, form):
        self.object = form.save()
        log_object_change(self.request.user, self.lab, self.object, 0, self.object.quantity,1,"Create", create=True)
        row = form.cleaned_data['row']
        col = form.cleaned_data['col']
        return {
            'inner-fragments': {
                '#row_%d_col_%d_shelf_%d' % (row, col, self.object.shelf.pk): list_shelfobject_render(
                    self.request, self.object.shelf.pk, row, col, lab_pk=self.lab),
                "#closemodal": '<script>$("#object_create").modal("hide");</script>'
            },
        }

    def get_form_kwargs(self):
        kwargs = CreateView.get_form_kwargs(self)
        kwargs['initial']['shelf'] = self.request.GET.get('shelf')
        kwargs['initial']['row'] = self.request.GET.get('row')
        kwargs['initial']['col'] = self.request.GET.get('col')
        return kwargs


@method_decorator(has_lab_assigned(), name="dispatch")
@method_decorator(permission_required('laboratory.change_shelfobject'), name='dispatch')
class ShelfObjectEdit(AJAXMixin, UpdateView):
    model = ShelfObject
    form_class = ShelfObjectFormUpdate
    success_url = "/"

    def get_success_url(self):
        return reverse_lazy('laboratory:list_shelf', args=(self.lab,))

    def form_valid(self, form):

        old = self.model.objects.filter(pk=self.object.id).values('quantity')[0]['quantity']
        self.object = form.save()
        log_object_change(self.request.user, self.lab, self.object, old, self.object.quantity,3,"Edit", create=False)

        row = form.cleaned_data['row']
        col = form.cleaned_data['col']
        return {
            'inner-fragments': {
                '#row_%d_col_%d_shelf_%d' % (row, col, self.object.shelf.pk):
                    list_shelfobject_render(
                        self.request, self.object.shelf.pk, row, col, lab_pk=self.lab),
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
        log_object_change(self.request.user, self.lab, self.object, old, self.object.quantity,3,"Update", create=False)
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
                         'laboratory': self.lab})
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
        return reverse_lazy('laboratory:list_shelf', args=(self.lab,))

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
                    request, row=self.row, col=self.col, shelf=self.object.shelf.pk, lab_pk=self.lab),
                "#closemodal": '<script>$("#object_delete").modal("hide");</script>'
            },
        }

@permission_required('laboratory.change_shelfobject')
def add_object(request,pk):
    """ The options represents several actions in numbers 1=Reservation, 2=Add, 3=Tranfer, 4=Subtract"""
    action = int(request.POST.get('options'))
    form = AddObjectForm(request.POST)

    if action == 2:
        if form.is_valid():
            try:
                amount = float(request.POST.get('amount'))
            except ValueError:
                return JsonResponse({'msg': False})
            object = ShelfObject.objects.filter(pk=request.POST.get('shelf_object')).first()
            old = object.quantity
            new = old+amount
            object.quantity = new
            object.save()
            log_object_add_change(request.user, pk, object, old, new,"Add", request.POST.get('provider'),request.POST.get('bill'), create=False)
            return JsonResponse({'msg': True})
        else:
            return JsonResponse({'msg': False})
    elif action == 4:
        return subtract_object(request, pk)
    else:
        return transfer_object(request,pk)
    return JsonResponse({'msg': True})

@permission_required('laboratory.change_shelfobject')
def subtract_object(request,pk):
    object = ShelfObject.objects.filter(pk=request.POST.get('shelf_object')).first()
    old = object.quantity
    form = SubtractObjectForm(request.POST)
    if form.is_valid():
        try:
            amount = float(form.cleaned_data['discount'])
        except ValueError:
            return JsonResponse({'msg': False})
        if old >= amount:
            new = old-amount
            object.quantity = new
            object.save()
            log_object_change(request.user, pk, object, old, new,3,"Substract", create=False)
        else:
            return JsonResponse({'msg': False})
    else:
        return JsonResponse({'msg': False})
    return JsonResponse({'msg': True})

def transfer_object(request,pk):
    try:
        amount = float(request.POST.get('amount_send'))
        print(amount)
    except ValueError:
        return JsonResponse({'msg': False})

    object = ShelfObject.objects.filter(pk=request.POST.get('shelf_object')).first()
    lab_send = Laboratory.objects.filter(pk=pk).first()
    lab_received = Laboratory.objects.filter(pk=request.POST.get('laboratory')).first()
    TranferObject.objects.create(object=object,
    laboratory_send = lab_send,
    laboratory_received = lab_received,
    quantify =amount
    )
    return JsonResponse({'msg': True})

@csrf_exempt
def send_detail(request):
    obj=ShelfObject.objects.get(pk=request.POST.get('shelf_object'))
    return JsonResponse({'obj': obj.get_object_detail()})

def list_tranfer_objects(request,pk):
    shelf=Shelf.objects.filter(furniture__labroom__laboratory__id=pk)

class ListTranferObjects(ListView):
    model = TranferObject
    template_name = 'laboratory/transfer_objects.html'

    def get_queryset(self):
        return TranferObject.objects.filter(Q(laboratory_send__id=self.request.GET.get('lab')) |
                                            Q(laboratory_received__id=self.request.GET.get('lab'))).order_by('update_time')

def get_shelf_list(request):
    shelfs = Shelf.objects.filter(furniture__labroom__laboratory__id=int(request.POST.get('lab')))
    aux=[]
    for shelf in shelfs:
        aux.append({'id':shelf.pk, 'shelf':shelf.get_shelf()})
    data=json.dumps(aux)
    return JsonResponse({'data': data})

def objects_transfer(request):
    data = TranferObject.objects.get(pk=int(request.POST.get('transfer_id')))
    object=data.object.object
    lab_received_obj=ShelfObject.objects.get(object_id=object.id, shelf_id=int(request.POST.get('shelf')))
    print(lab_received_obj)
    return JsonResponse({'data': True})