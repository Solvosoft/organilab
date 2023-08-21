# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''

from django import forms
from django.conf import settings
from django.contrib.admin.models import DELETION, ADDITION, CHANGE
from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.urls.base import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django_ajax.decorators import ajax
from django_ajax.mixin import AJAXMixin
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets import wysiwyg
from djgentelella.widgets.selects import AutocompleteSelectMultiple
from rest_framework import status

from auth_and_perms.organization_utils import user_is_allowed_on_organization, \
    organization_can_change_laboratory
from laboratory.models import Shelf, Object, Laboratory, OrganizationStructure
from presentation.utils import build_qr_instance
from .djgeneric import CreateView, UpdateView
from ..utils import organilab_logentry


@ajax
@permission_required('laboratory.delete_shelf')
def delete_shelf(request, org_pk, lab_pk, pk, row, col):
    laboratory = get_object_or_404(Laboratory.objects.using(settings.READONLY_DATABASE), pk=lab_pk)
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    organization_can_change_laboratory(laboratory, organization)

    if request.method == 'POST':
        shelf = get_object_or_404(Shelf, pk=pk)
        furniture = shelf.furniture
        furniture.remove_shelf_dataconfig(pk)
        shelf.delete()
        organilab_logentry(request.user, shelf, DELETION, relobj=lab_pk)
        return JsonResponse({"result": "OK"}, status=status.HTTP_200_OK)

    row, col = int(row), int(col)
    url = reverse('laboratory:shelf_delete', kwargs={"lab_pk": lab_pk, "pk":pk, "row": row,
                                                     "col": col,"org_pk": org_pk})
    return {'inner-fragments': {
        "#modalclose": """<script>delete_shelf("#shelf_%s", "%s");</script>""" % (pk, url)
    },}


class ShelfForm(forms.ModelForm, GTForm):
    col = forms.IntegerField(widget=forms.HiddenInput)
    row = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk')
        super().__init__(*args, **kwargs)
        self.fields['available_objects_when_limit'] = forms.ModelMultipleChoiceField(
            queryset=Object.objects.all(),
            required=False,
            widget=AutocompleteSelectMultiple('objectorgavailable', attrs={
                'data-dropdownparent': "#createshelfmodal",
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization',

            }))

    class Meta:
        model = Shelf
        fields = ['name', 'type', 'furniture', 'color','discard','infinity_quantity','quantity','measurement_unit','description',
                  'limit_only_objects', 'available_objects_when_limit']
        widgets = {
            'name': genwidgets.TextInput,
            'type': genwidgets.SelectWithAdd(attrs={'add_url': reverse_lazy('laboratory:add_shelf_type_catalog')}),
            'furniture': forms.HiddenInput(),
            'color':  genwidgets.ColorInput,
            'discard': genwidgets.CheckboxInput,
            'infinity_quantity': genwidgets.CheckboxInput,
            'quantity': genwidgets.TextInput,
            'measurement_unit': genwidgets.Select,
            'description': wysiwyg.TextareaWysiwyg,
            'limit_only_objects': genwidgets.CheckboxInput,

        }

    def clean(self):
        discard= self.cleaned_data['discard']
        quantity = self.cleaned_data['quantity']
        unit = self.cleaned_data['measurement_unit']
        infinity = self.cleaned_data['infinity_quantity']
        if discard:
            if unit is not None and quantity <= 0 and not infinity:
                self.add_error('quantity', _("The quantity need to be greater than 0"))
        elif unit is not None and quantity <= 0 and not infinity:
            self.add_error('quantity', _("The quantity need to be greater than 0"))
        elif quantity<0:
            self.add_error('quantity', _("The quantity need to be greater than 0"))

        if unit == None and quantity <= 0 and not infinity:
            self.add_error('quantity',_("The quantity need to be greater than 0, when dont select an unit and check the field infinity quantity."))
            self.add_error('measurement_unit', _('Need a unit when the dont check the field infinity quantity.'))

    def clean_measurement_unit(self):
        discard = self.cleaned_data['discard']
        unit = self.cleaned_data['measurement_unit']
        infinity = self.cleaned_data['infinity_quantity']

        if unit is None and discard and not infinity:
            self.add_error('measurement_unit', _('When a shelf if discard you need to add a measurement unit'))

        return unit



class ShelfUpdateForm(forms.ModelForm, GTForm):
    col = forms.IntegerField(widget=forms.HiddenInput)
    row = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk')
        super().__init__(*args, **kwargs)
        self.fields['available_objects_when_limit'] = forms.ModelMultipleChoiceField(
            queryset=Object.objects.all(),
            required=False,
            widget=AutocompleteSelectMultiple('objectorgavailable', attrs={
                'data-dropdownparent': "#createshelfmodal",
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization',

            }))

    class Meta:
        model = Shelf
        fields = ['name', 'type', 'furniture', 'color','discard','infinity_quantity','quantity','measurement_unit','description',
                  'limit_only_objects', 'available_objects_when_limit']
        widgets = {
            'name': genwidgets.TextInput,
            'type': genwidgets.SelectWithAdd(attrs={'add_url': reverse_lazy('laboratory:add_shelf_type_catalog')}),
            'furniture': forms.HiddenInput(),
            'color':  genwidgets.ColorInput,
            'discard': genwidgets.CheckboxInput,
            'infinity_quantity': genwidgets.CheckboxInput,
            'quantity': genwidgets.TextInput,
            'measurement_unit': genwidgets.Select,
            'description': wysiwyg.TextareaWysiwyg,
            'limit_only_objects': genwidgets.CheckboxInput,
        }

    def clean_measurement_unit(self):
        discard = self.cleaned_data['discard']
        infinity = self.cleaned_data['infinity_quantity']
        unit = self.cleaned_data['measurement_unit']
        quantity = self.cleaned_data['quantity']
        shelfobjects = self.instance.get_objects().count()
        change_unit = unit != self.instance.measurement_unit

        if shelfobjects>0 and change_unit:
            self.add_error('measurement_unit',_("The shelf have objects need to removed them, before changes the measurement unit"))
        elif unit==None and infinity==False and quantity<=0:
            self.add_error('quantity',_("The quantity need to be greater than 0, when dont select an unit and check the field infinity quantity."))
            self.add_error('measurement_unit', _('Need a unit when the dont check the field infinity quantity.'))
        if discard:
            if unit != None:
                return unit
            else:
                self.add_error('measurement_unit',_("Need add the measurement unit"))
        else:
            return unit

        return unit


    def clean_quantity(self):
        discard = self.cleaned_data['discard']
        quantity = self.cleaned_data['quantity']
        infinity_quantity = self.cleaned_data['infinity_quantity']
        amount = quantity >= self.instance.get_total_refuse() #get_total_refuse return the amount that the shelf have about shelfobjects
        if discard:
            if amount and quantity > 0:
                return quantity
            else:
                self.add_error('quantity', _('The quantity is less than the amount to the sum the objects'))

        if amount or infinity_quantity:
            return quantity
        else:
            self.add_error('quantity', _('The quantity is less than the amount to the sum the objects'))

        return quantity





@method_decorator(permission_required('laboratory.add_shelf'), name='dispatch')
class ShelfCreate(AJAXMixin, CreateView):
    model = Shelf
    success_url = "/"
    form_class = ShelfForm

    def get_prefix(self):
        return "shelf-"


    def get_form_kwargs(self):
        kwargs = CreateView.get_form_kwargs(self)
        kwargs['org_pk'] = self.org
        kwargs['initial']['furniture'] = self.request.GET.get('furniture')
        kwargs['initial']['col'] = self.request.GET.get('col')
        kwargs['initial']['row'] = self.request.GET.get('row')
        return kwargs


    def generate_qr(self):
        schema = self.request.scheme + "://"
        domain = schema + self.request.get_host()
        url = domain + reverse('laboratory:rooms_list', kwargs={"org_pk": self.org,
                                                                "lab_pk": self.lab})
        url = url + "#labroom=%d&furniture=%d&shelf=%d" % (self.object.furniture.labroom.pk,
                                                           self.object.furniture.pk, self.object.pk)
        build_qr_instance(url, self.object, self.org)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        furniture = form.cleaned_data['furniture']
        col = form.cleaned_data['col']
        row = form.cleaned_data['row']
        if furniture is None or col is None or row is None:
            return self.form_invalid(form)
        try:
            col, row = int(col), int(row)
        except:
            return self.form_invalid(form)

        self.object.furniture = furniture
        self.object.created_by = self.request.user
        self.object.save()
        if form.cleaned_data['limit_only_objects']:
            for objlimt in form.cleaned_data['available_objects_when_limit']:
                self.object.available_objects_when_limit.add(objlimt)
        else:
            self.object.available_objects_when_limit.clear()
        self.generate_qr()
        organilab_logentry(self.request.user, self.object, ADDITION, 'shelf', changed_data=form.changed_data,
                           relobj=self.lab)

        dev = render_to_string(
            "laboratory/shelf_details.html",
            {"crow": row,
             "ccol": col,
             "data": self.object,
             "org_pk": self.org,
             "laboratory": self.lab}, request=self.request)
        return {
            'inner-fragments': {
                "#modalclose": "<script>closeModal();</script>"
            },
            'append-fragments': {
                '#row_%d_col_%d ul.sortableself' % (row, col): dev,
            }
        }

    def form_invalid(self, form):
        response = CreateView.form_invalid(self, form)
        response.render()
        return {
            'inner-fragments': {
                '#shelfmodalbody': response.content,
                "#modalclose": "<script>refresh_description();</script>",
            }
        }


@method_decorator(permission_required('laboratory.change_shelf'), name='dispatch')
class ShelfEdit(AJAXMixin, UpdateView):
    model = Shelf
    success_url = "/"
    form_class = ShelfUpdateForm

    def get_prefix(self):
        return "shelf-"

    def get(self, request, *args, **kwargs):
        self.row = kwargs.pop('row')
        self.col = kwargs.pop('col')
        return UpdateView.get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.row = kwargs.pop('row')
        self.col = kwargs.pop('col')
        return UpdateView.post(self, request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(ShelfEdit, self).get_form_kwargs()
        kwargs['org_pk'] = self.org
        kwargs['initial']['furniture'] = self.request.GET.get('furniture')
        kwargs['initial']['col'] = self.col
        kwargs['initial']['row'] = self.row
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        furniture = form.cleaned_data['furniture']
        col = self.col or form.cleaned_data['col']
        row = self.row or form.cleaned_data['row']
        if furniture is None or col is None or row is None:
            return self.form_invalid(form)
        try:
            col, row = int(col), int(row)
        except:
            return self.form_invalid(form)

        self.object.furniture = furniture
        self.object.save()
        if form.cleaned_data['limit_only_objects']:
            self.object.available_objects_when_limit.clear()
            for objlimt in form.cleaned_data['available_objects_when_limit']:
                self.object.available_objects_when_limit.add(objlimt)
        else:
            self.object.available_objects_when_limit.clear()
        organilab_logentry(self.request.user, self.object, CHANGE, changed_data=form.changed_data, relobj=self.lab)

        dev = render_to_string(
            "laboratory/shelf_details.html",
            {"crow": row,
             "ccol": col,
             "data": self.object,
             "org_pk": self.org,
             "laboratory": self.lab}, request=self.request)

        return {
            'inner-fragments': {
                "#modalclose": "<script>closeModal();</script>"
            },
            'fragments': {
                '#shelf_%s' % (self.object.pk): dev,
            }
        }

    def form_invalid(self, form):
        response = UpdateView.form_invalid(self, form)
        response.render()
        return {
            'inner-fragments': {
                '#shelfmodalbody': response.content,
                "#modalclose": "<script>refresh_description();</script>",
            }
        }


class RemoveShelfForm(forms.Form):
    shelfs=forms.ModelMultipleChoiceField(queryset=Shelf.objects.all())
