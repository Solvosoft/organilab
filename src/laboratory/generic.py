'''
Created on 11/8/2016

@author: natalia
'''

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView
from laboratory.models import Shelf


@method_decorator(login_required, name='dispatch')
class ShelfListView(ListView):
    model = Shelf
