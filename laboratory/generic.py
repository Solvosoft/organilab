'''
Created on 11/8/2016

@author: natalia
'''
from __future__ import unicode_literals

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy, reverse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from django_ajax.decorators import ajax
from django_ajax.mixin import AJAXMixin

from laboratory.models import Shelf, Object


@method_decorator(login_required, name='dispatch')
class ShelfListView(ListView):
    model = Shelf
