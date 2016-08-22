'''
Created on 17/8/2016

@author: nashyra
'''
from django_ajax.decorators import ajax
from laboratory.models import Shelf, Furniture, Object, ObjectFeatures, LaboratoryRoom
from django.template.loader import render_to_string
from django_ajax.mixin import AJAXMixin
from django.views.generic.edit import CreateView, DeleteView
from django.core.urlresolvers import reverse_lazy
from django.http.response import HttpResponseRedirect
from django.template.context_processors import request

class FurnitureCreate(CreateView):
    model = Furniture
    fields = '__all__'
    success_url = "/"


def list_shelf_render(request):
    shelves = Shelf.objects.all()
    return render_to_string(
        'laboratory/shelf_list.html',
        context={
                 'object_list': shelves
        })
    
@ajax
def list_shelf(request):
    return {
        'inner-fragments': {
            '#shelves': list_shelf_render(request)
        },
    }
    
class ShelvesCreate(AJAXMixin, CreateView):
    model = Shelf
    fields = "__all__"
    success_url = reverse_lazy('shelf_list')
    
    def post(self, request, *args, **kwargs):
        response = CreateView.post(self, request, *args, **kwargs)
        
        if type(response) == HttpResponseRedirect:
            return list_shelf_render(request)
        
        return response
