'''
Created on 11/8/2016

@author: natalia
'''
from __future__ import unicode_literals

from django.views.generic.edit import CreateView, DeleteView, UpdateView
from laboratory.models import Shelf, Object, LaboratoryRoom, Furniture, Laboratory
from django.views.generic.list import ListView
from django.core.urlresolvers import reverse_lazy, reverse
from django.db.models.query import QuerySet
from django_ajax.mixin import AJAXMixin
from django import forms
import json
from django_ajax.decorators import ajax
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404


class ObjectDeleteFromShelf(DeleteView):
    model = Object
    success_url = reverse_lazy('laboratory:object-list')


@method_decorator(login_required, name='dispatch')
class ObjectList(ListView):
    model = Object


@method_decorator(login_required, name='dispatch')
class ObjectCreate(CreateView):
    model = Object
    fields = '__all__'
    success_url = "/"


@method_decorator(login_required, name='dispatch')
class LaboratoryRoomsList(ListView):
    model = LaboratoryRoom

    def get_queryset(self):
        if 'lab_pk' in self.kwargs:
            lab = Laboratory.objects.get(pk=self.kwargs.get('lab_pk'))
            return lab.rooms.all()
        else:
            return super(LaboratoryRoomsList, self).get_queryset()

    def get_context_data(self, **kwargs):
        context = super(LaboratoryRoomsList, self).get_context_data(**kwargs)
        return context


@method_decorator(login_required, name='dispatch')
class LabroomCreate(CreateView):
    model = LaboratoryRoom
    fields = '__all__'
    success_url = reverse_lazy('laboratory:laboratoryroom_create')

    def get_context_data(self, **kwargs):
        context = CreateView.get_context_data(self, **kwargs)

        if 'lab_pk' in self.kwargs:
            lab = Laboratory.objects.get(pk=self.kwargs.get('lab_pk'))
            context['object_list'] = lab.rooms.all()
        else:
            context['object_list'] = self.model.objects.all()
        return context

    def form_valid(self, form):
        if 'lab_pk' in self.kwargs:
            room = form.save()
            lab = Laboratory.objects.get(pk=self.kwargs.get('lab_pk'))
            lab.rooms.add(room)
            lab.save()
        return super(LabroomCreate, self).form_valid(form)

    def get_success_url(self):
        if 'lab_pk' in self.kwargs:
            return reverse_lazy('laboratory:laboratory_rooms_create', kwargs={'lab_pk': self.kwargs.get('lab_pk')})

        return super(LabroomCreate, self).get_success_url()


class LaboratoryRoomDelete(DeleteView):
    model = LaboratoryRoom
    success_url = reverse_lazy('laboratory:laboratoryroom_create')

    def get_success_url(self):
        if 'lab_pk' in self.kwargs:
            return reverse_lazy('laboratory:laboratory_rooms_create', kwargs={'lab_pk': self.kwargs.get('lab_pk')})

        return super(LaboratoryRoomDelete, self).get_success_url()


@method_decorator(login_required, name='dispatch')
class LabRoomList(ListView):
    model = LaboratoryRoom


class ShelfForm(forms.ModelForm):
    col = forms.IntegerField(widget=forms.HiddenInput)
    row = forms.IntegerField(widget=forms.HiddenInput)

    class Meta:
        model = Shelf
        fields = ['name', 'type', 'furniture']
        widgets = {
            'furniture': forms.HiddenInput()
        }


@method_decorator(login_required, name='dispatch')
class ShelfCreate(AJAXMixin, CreateView):
    model = Shelf
    success_url = "/"
    form_class = ShelfForm

    def get_form_kwargs(self):
        kwargs = CreateView.get_form_kwargs(self)
        kwargs['initial']['furniture'] = self.request.GET.get('furniture')
        kwargs['initial']['col'] = self.request.GET.get('col')
        kwargs['initial']['row'] = self.request.GET.get('row')
        return kwargs

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
        self.object.save()

        dev = render_to_string(
            "laboratory/shelf_details.html",
            {"crow": row,
             "ccol": col,
             "data": self.object})
        return {
            'inner-fragments': {
                "#modalclose": "<script>closeModal();</script>"
            },
            'append-fragments': {
                '#row_%d_col_%d ul' % (row, col): dev,
            }
        }

    def form_invalid(self, form):
        response = CreateView.form_invalid(self, form)
        response.render()
        return {
            'inner-fragments': {
                '#shelfmodalbody': response.content
            }
        }


@method_decorator(login_required, name='dispatch')
class ShelfEdit(AJAXMixin, UpdateView):
    model = Shelf
    success_url = "/"
    form_class = ShelfForm

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

        dev = render_to_string(
            "laboratory/shelf_details.html",
            {"crow": row,
             "ccol": col,
             "data": self.object})

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
                '#shelfmodalbody': response.content
            }
        }


@login_required
@ajax
def ShelfDelete(request, pk, row, col):
    row, col = int(row), int(col)
    shelf = get_object_or_404(Shelf, pk=pk)
    shelf.delete()
    url = reverse('laboratory:shelf_delete', args=(pk, row, col))
    # url = url.replace("/", "\\/")
    print(url)
    return {'inner-fragments': {
        "#modalclose": """<script>$("a[href$='%s']").closest('li').remove();</script>""" % (url)
    },}


@method_decorator(login_required, name='dispatch')
class ShelfListView(ListView):
    model = Shelf
