'''
Created on 1/8/2016

@author: nashyra
'''
from django.views.generic import CreateView
from laboratory.models import Furniture


class FurnitureCreateView(CreateView):
    model = Furniture
    success_url = '/'
    fields = '__all__'