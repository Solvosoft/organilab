'''
Created on 1/8/2016

@author: nashyra
'''

from __future__ import unicode_literals

from django.views.generic.edit import CreateView, DeleteView
from laboratory.models import Shelf, LaboratoryRoom, Object, LaboratoryRoom
from django.contrib.messages.api import success
from django.views.generic.list import ListView
from django.core.urlresolvers import reverse_lazy
from django.db.models.query import QuerySet   

class LabroomCreate(CreateView):
    model = LaboratoryRoom
    fields = '__all__'
    success_url = "/"

class ObjectCreate(CreateView):
    model = Object
    fields = '__all__'
    success_url = "/"

class ShelfCreate(CreateView):
    model = Shelf
    fields = '__all__'
    success_url = "/"

class ShelfDelete(DeleteView):
    model = Shelf
    success_url = reverse_lazy('object-list')

class LabRoomList(ListView):
    model = LaboratoryRoom
    
class ShelfListView(ListView):
    model = Shelf
    
    def get_queryset(self):
        queryset = ListView.get_queryset(self)
        queryset = queryset.filter(container_shelf__gte=5)
        return queryset