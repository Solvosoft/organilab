# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''

from django import forms
from django.contrib.auth.decorators import login_required
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls.base import reverse
from django.utils.decorators import method_decorator
from django_ajax.decorators import ajax
from django_ajax.mixin import AJAXMixin

from laboratory.models import Furniture, Shelf
from laboratory.shelf_utils import get_dataconfig

from .djgeneric import CreateView, UpdateView

from laboratory.decorators import user_group_perms


def get_shelves(furniture):
    if type(furniture) == QuerySet:
        furniture = furniture[0]

    if furniture.dataconfig:
        return get_dataconfig(furniture.dataconfig)


@login_required
def list_shelf_render(request, lab_pk):
    var = request.GET.get('furniture', '0')
    furniture = Furniture.objects.filter(pk=var)
    shelf = get_shelves(furniture)

    return render_to_string(
        'laboratory/shelf_list.html',
        context={
            'object_list': shelf,
            'laboratory': lab_pk,
            'request': request
        })


@login_required
@ajax
def list_shelf(request, lab_pk):
    return {
        'inner-fragments': {
            '#shelf': list_shelf_render(request, lab_pk)

        },
    }


@login_required
@ajax
def ShelfDelete(request, lab_pk, pk, row, col):
    row, col = int(row), int(col)
    shelf = get_object_or_404(Shelf, pk=pk)
    shelf.delete()
    url = reverse('laboratory:shelf_delete', args=(lab_pk, pk, row, col))
    return {'inner-fragments': {
        "#modalclose": """<script>$("a[href$='%s']").closest('li').remove();</script>""" % (url)
    },}


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
@method_decorator(user_group_perms(perm='laboratory.add_shelf'), name='dispatch')
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
             "data": self.object,
             "laboratory": self.lab})
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
@method_decorator(user_group_perms(perm='laboratory.change_shelf'), name='dispatch')
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
             "data": self.object,
             "laboratory": self.lab})

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
