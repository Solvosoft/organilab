'''
Created on 13 Sept. 2018

@author: Guillermo
'''

# Import functions of another modules
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _
from .models import Sustance
import json
from django.http import HttpResponse

# SGA Home Page


def index_sga(request):
    return render(request, 'index_sga.html', {})

# SGA Pre Editor Page


def pre_editor(request):
    return render(request, 'pre_editor.html', {})

# SGA Search sustance with autocomplete


def search_autocomplete_sustance(request):
    if request.is_ajax():
        q = request.GET.get('term', '')
        # Contains the typed characters, is valid since the first character
        # Search Parameter: Comercial Name
        search_qs = Sustance.objects.filter(comercial_name__icontains=q)
        results = []
        for r in search_qs:
            results.append(r.comercial_name)
        data = json.dumps(results)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)