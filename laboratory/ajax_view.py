'''
Created on /8/2016

@author: natalia
'''
from laboratory.models import Furniture, Shelf, ShelfObject, ObjectFeatures
from django.template.loader import render_to_string
from django_ajax.decorators import ajax
from django_ajax.mixin import AJAXMixin
from django.views.generic.edit import CreateView, DeleteView
from django.urls.base import reverse_lazy
from django.http.response import HttpResponseRedirect
from django.template.context_processors import request


def get_shelves(furniture):
    # import json
    # dev =  json.loads(furniture.dataconfig)
    # hacer algo para pasar de num a shelf
    return [["", 3, ""],
            [1, "", ""],
            ["", 5, ""]
            ]


def list_furniture_render(request):

    var = request.GET.get('namelaboratoryRoom', '0')
    print(' _________________   ' + var + '   __________namelaboratoryRoom')

    if var:
        furnitures = Furniture.objects.filter(labroom=var)
    else:
        furnitures = Furniture.objects.all()
    return render_to_string(
        'laboratory/furniture_list.html',
        context={
            'object_list': furnitures
        })


@ajax
def list_furniture(request):
   # print("Entro al ajax_view labory furniture")
    return {
        'inner-fragments': {
            '#furnitures': list_furniture_render(request)

        },
    }


def list_shelf_render(request):
    var = request.GET.get('furniture', '0')
    print(' _________________   ' + var + '   __________furniture')

    furniture = Furniture.objects.filter(pk=var)
    shelf = get_shelves(furniture)

    return render_to_string(
        'laboratory/shelf_list.html',
        context={
            'object_list': shelf
        })


@ajax
def list_shelf(request):
    print("Entro al ajax_view laboryyyyyyyyyyyyyyyyy shelf")
    return {
        'inner-fragments': {
            '#shelf': list_shelf_render(request)

        },
    }


def list_shelfobject_render(request):
    var = request.GET.get('shelf', '0')

    print(' _________________   ' + var + '   __________shelf')

    if var:
        shelfobject = ShelfObject.objects.filter(object=var)
    else:
        shelfobject = ShelfObject.objects.all()
    return render_to_string(
        'laboratory/shelfObject_list.html',
        context={
            'object_list': shelfobject
        })


@ajax
def list_shelfobject(request):
    print("Entro al ajax_view laboryyyyyyyyyyyyyyyyy shelfObject")
    return {
        'inner-fragments': {
            '#shelfobject': list_shelfobject_render(request),
            '#shelfposition': request.GET.get('shelf', '0'),
            '#shelfposition1': request.GET.get('shelf', '0')

        },
    }


class ShelfObjectCreate(AJAXMixin, CreateView):
    model = ShelfObject
    fields = "__all__"
    success_url = reverse_lazy('laboratory:list_shelf')

    def post(self, request, *args, **kwargs):
        response = CreateView.post(self, request, *args, **kwargs)

        if type(response) == HttpResponseRedirect:
            return list_shelfobject_render(request)

        return response


class ShelfObjectDelete(AJAXMixin, DeleteView):
    model = ShelfObject
    success_url = reverse_lazy('laboratory:list_shelf')

    def post(self, request, *args, **kwargs):
        response = DeleteView.post(self, request, *args, **kwargs)

        if type(response) == HttpResponseRedirect:
            return list_shelfobject_render(request)

        return response


def admin_list_shelf_render(request):
    shelves = Shelf.objects.all()
    return render_to_string(
        'laboratory/admin_shelf_list.html',
        context={
            'object_list': shelves
        })


@ajax
def admin_list_shelf(request):
    return {
        'inner-fragments': {
            '#shelves': list_shelf_render(request)
        },
    }


class ShelvesCreate(AJAXMixin, CreateView):
    model = Shelf
    fields = "__all__"
    success_url = reverse_lazy('laboratory:list_shelf')

    def post(self, request, *args, **kwargs):
        response = CreateView.post(self, request, *args, **kwargs)

        if type(response) == HttpResponseRedirect:
            return list_shelf_render(request)

        return response


def list_objectfeatures_render(request):
    objectfeatures = ObjectFeatures.objects.all()
    return render_to_string(
        'laboratory/objectfeatures_list.html',
        context={
            'object_list': objectfeatures
        })


@ajax
def list_objectfeatures(request):
    return {
        'inner-fragments': {
            '#objectfeatures': list_objectfeatures_render(request)
        },
    }


class ObjectFeaturesCreate(AJAXMixin, CreateView):
    model = ObjectFeatures
    fields = "__all__"
    success_url = reverse_lazy('laboratory:objectfeatures_list')

    def post(self, request, *args, **kwargs):
        response = CreateView.post(self, request, *args, **kwargs)

        if type(response) == HttpResponseRedirect:
            return list_objectfeatures_render(request)

        return response
