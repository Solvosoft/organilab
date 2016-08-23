'''
Created on 1/8/2016

@author: nashyra
'''
from django.shortcuts import render
from django.views.generic import CreateView
from laboratory.models import Furniture


def index(request):
    return render(request, 'laboratory/index.html')


class FurnitureCreateView(CreateView):
    model = Furniture
    success_url = '/'
    fields = '__all__'
