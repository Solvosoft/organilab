'''
Created on 11/8/2016

@author: natalia
'''
from __future__ import unicode_literals
from django.views.generic.edit import DeleteView
from django.core.urlresolvers import reverse_lazy
from django.views.generic.list import ListView
from django.db.models.query import QuerySet
from laboratory.models import Object, LaboratoryRoom



class ObjectDeleteFromShelf(DeleteView):
    model= Object
    success_url = reverse_lazy('object-list')

class ObjectList(ListView):
    model = Object

class LaboratoryRoomsList(ListView):
    model = LaboratoryRoom
    
    
