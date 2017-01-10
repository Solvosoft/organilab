# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''
from __future__ import unicode_literals

from django import forms
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseRedirect
from django.template.loader import render_to_string
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator
from django_ajax.decorators import ajax
from django_ajax.mixin import AJAXMixin

from laboratory.models import ShelfObject, Shelf

from .djgeneric import CreateView, UpdateView, DeleteView


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
            'laboratory': lab_pk
        })


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


class ShelfObjectForm(forms.ModelForm):
    col = forms.IntegerField(widget=forms.HiddenInput)
    row = forms.IntegerField(widget=forms.HiddenInput)

    class Meta:
        model = ShelfObject
        fields = "__all__"
        widgets = {
            'shelf': forms.HiddenInput,
        }


class ShelfObjectFormUpdate(forms.ModelForm):
    col = forms.IntegerField(widget=forms.HiddenInput, required=False)
    row = forms.IntegerField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = ShelfObject
        fields = ['shelf', 'quantity', 'limit_quantity', 'measurement_unit']
        widgets = {
            'shelf': forms.HiddenInput,
        }


@method_decorator(login_required, name='dispatch')
class ShelfObjectCreate(AJAXMixin, CreateView):
    model = ShelfObject
    form_class = ShelfObjectForm
    success_url = "/"

    def get_success_url(self):
        return reverse_lazy('laboratory:list_shelf', args=(self.lab,))

    def form_valid(self, form):
        self.object = form.save()
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


@method_decorator(login_required, name='dispatch')
class ShelfObjectEdit(AJAXMixin, UpdateView):
    model = ShelfObject
    form_class = ShelfObjectFormUpdate
    success_url = "/"

    def get_success_url(self):
        return reverse_lazy('laboratory:list_shelf', args=(self.lab,))

    def form_valid(self, form):
        self.object = form.save()
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


@method_decorator(login_required, name='dispatch')
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
        return UpdateView.form_valid(self, form)

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


@method_decorator(login_required, name='dispatch')
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
        self.row = request.POST.get("row")
        self.col = request.POST.get("col")

        return {
            'inner-fragments': {
                '#row_%s_col_%s_shelf_%d' % (self.row, self.col, self.object.shelf.pk): list_shelfobject_render(
                    request, row=self.row, col=self.col, shelf=self.object.shelf.pk, lab_pk=self.lab),
                "#closemodal": '<script>$("#object_delete").modal("hide");</script>'
            },
        }