'''
Created on 11/8/2016

@author: natalia
'''
from __future__ import unicode_literals

from django.views.generic.edit import CreateView, DeleteView
from laboratory.models import Shelf, Object, LaboratoryRoom, Furniture
from django.views.generic.list import ListView
from django.core.urlresolvers import reverse_lazy
from django.db.models.query import QuerySet
from django_ajax.mixin import AJAXMixin
from django import forms
import json
from django_ajax.decorators import ajax
from django.template.loader import render_to_string


class ObjectDeleteFromShelf(DeleteView):
    model = Object
    success_url = reverse_lazy('laboratory:object-list')


class ObjectList(ListView):
    model = Object


class LaboratoryRoomsList(ListView):
    model = LaboratoryRoom


class LabroomCreate(CreateView):
    model = LaboratoryRoom
    fields = '__all__'
    success_url = reverse_lazy('laboratory:object-list')


class ObjectCreate(CreateView):
    model = Object
    fields = '__all__'
    success_url = "/"


class ShelfForm(forms.ModelForm):
    col = forms.IntegerField(widget=forms.HiddenInput)
    row = forms.IntegerField(widget=forms.HiddenInput)

    class Meta:
        model = Shelf
        fields = ['type', 'furniture']
        widgets = {
            'furniture': forms.HiddenInput()
        }


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
        dataconfig = self.set_dataconfig(furniture,
                                         col, row,
                                         self.object.pk)

        dev = render_to_string(
            "laboratory/shelf_rows.html",
            {"crow": row,
             "ccol": col,
             "col": Shelf.objects.filter(
                 pk__in=dataconfig[row][col].split(","))})

        return {
            'inner-fragments': {
                '#row_%d_col_%d' % (row, col): dev,
                "#modalclose": "<script>closeModal();</script>"
            },
        }

    def set_dataconfig(self, furniture, col, row, value):
        dataconfig = self.build_dataconfig(furniture, col, row)
        if dataconfig[row][col]:
            dataconfig[row][col] += ","
        dataconfig[row][col] += str(value)
        furniture.dataconfig = json.dumps(dataconfig)
        furniture.save()
        return dataconfig

    def build_dataconfig(self, furniture, col, row):
        if furniture.dataconfig:
            dataconfig = json.loads(furniture.dataconfig)
        else:
            dataconfig = []
        if len(dataconfig) > 0:
            # Work with rows
            row2 = len(dataconfig) - 1
            col2 = len(dataconfig[0]) - 1
            if row2 < row:
                row_less = row - row2
                print(row_less, row, row2)
                for x in range(row_less):
                    dataconfig.append([''] * (col2 + 1))
            # Work with columns
            if col2 < col:
                col_less = col - col2
                print(col_less, col, row)
                for i, x in enumerate(dataconfig):
                    dataconfig[i] = dataconfig[i] + [''] * col_less
        else:
            for x in range(row + 1):
                dataconfig.append([''] * (col + 1))
        return dataconfig


@ajax
def ShelfDelete(request, pk, row, col):
    row, col = int(row), int(col)
    shelf = Shelf.objects.get(pk=pk)
    furniture = shelf.furniture
    dataconfig = json.loads(furniture.dataconfig)
    dev = ""
    if len(dataconfig) > 0 and len(dataconfig) > row and \
            len(dataconfig[0]) > col:
        data = dataconfig[row][col].split(",")
        if str(pk) in data:
            data.remove(str(pk))
            dataconfig[row][col] = ",".join(data)

            dev = render_to_string(
                "laboratory/shelf_rows.html",
                {"crow": row,
                 "ccol": col,
                 "col": Shelf.objects.filter(pk__in=data)})
        furniture.dataconfig = json.dumps(dataconfig)
        furniture.save()

    shelf.delete()
    return {'inner-fragments': {
        '#row_%d_col_%d' % (row, col): dev
    }, }


class LabRoomList(ListView):
    model = LaboratoryRoom


class ShelfListView(ListView):
    model = Shelf

#     def get_queryset(self):
#         queryset = ListView.get_queryset(self)
#         queryset = queryset.filter(container_shelf__gte=5)
#         return queryset
