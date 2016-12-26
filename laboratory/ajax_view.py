'''
Created on /8/2016

@author: natalia
'''
from django import forms
from django.contrib.auth.decorators import login_required
from django.db.models.query import QuerySet
from django.http.response import HttpResponseRedirect
from django.template.loader import render_to_string
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from django_ajax.decorators import ajax
from django_ajax.mixin import AJAXMixin
from laboratory.decorators import verify_laboratory_session
from laboratory.models import Furniture, Shelf, ShelfObject, ObjectFeatures
from laboratory.shelf_utils import get_dataconfig


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
            'laboratory': lab_pk
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
def admin_list_shelf_render(request):
    shelves = Shelf.objects.all()
    return render_to_string(
        'laboratory/admin_shelf_list.html',
        context={
            'object_list': shelves
        })


@login_required
@ajax
def admin_list_shelf(request):
    return {
        'inner-fragments': {
            '#shelves': list_shelf_render(request)
        },
    }


@method_decorator(login_required, name='dispatch')
class ShelvesCreate(AJAXMixin, CreateView):
    model = Shelf
    fields = "__all__"
    success_url = reverse_lazy('laboratory:list_shelf')

    def post(self, request, *args, **kwargs):
        response = CreateView.post(self, request, *args, **kwargs)

        if type(response) == HttpResponseRedirect:
            return list_shelf_render(request)

        return response


@login_required
def list_objectfeatures_render(request):
    objectfeatures = ObjectFeatures.objects.all()
    return render_to_string(
        'laboratory/objectfeatures_list.html',
        context={
            'object_list': objectfeatures
        })


@login_required
@ajax
def list_objectfeatures(request):
    return {
        'inner-fragments': {
            '#objectfeatures': list_objectfeatures_render(request)
        },
    }


@method_decorator(login_required, name='dispatch')
class ObjectFeaturesCreate(AJAXMixin, CreateView):
    model = ObjectFeatures
    fields = "__all__"
    success_url = reverse_lazy('laboratory:objectfeatures_list')

    def post(self, request, *args, **kwargs):
        response = CreateView.post(self, request, *args, **kwargs)

        if type(response) == HttpResponseRedirect:
            return list_objectfeatures_render(request)

        return response
