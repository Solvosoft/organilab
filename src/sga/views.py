'''
@organization: Solvo
@license: GNU General Public License v3.0
@date: Created on 13 sept. 2018
@author: Guillermo Castro Sánchez
@email: guillermoestebancs@gmail.com
'''

# Import functions of another modules
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _
from .models import Sustance, Component
from django.http import HttpResponse
from django.db.models.query_utils import Q
import json

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
        # Search Parameter: Comercial Name or CAS Number
        if(any(c.isalpha() for c in q)):
            search_qs = Sustance.objects.filter(Q(comercial_name__icontains=q) | Q(synonymous__icontains=q))
        else:
            search_qs = Sustance.objects.filter(components__cas_number__icontains=q)
        results = []
        for r in search_qs:
            results.append(r.comercial_name+' : '+r.synonymous)
        if(not results):
            results.append('No results')
        data = json.dumps(results)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)