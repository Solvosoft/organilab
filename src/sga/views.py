'''
@organization: Solvo
@license: GNU General Public License v3.0
@date: Created on 13 sept. 2018
@author: Guillermo Castro Sánchez
@email: guillermoestebancs@gmail.com
'''

# Import functions of another modules
from django import forms
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _
from .models import Sustance, Component, RecipientSize, DangerIndication
from django.http import HttpResponse
from django.db.models.query_utils import Q
import json
import logging
from django.template import Template, Library
from rest_framework import serializers
from django.core import serializers
from django.http import JsonResponse
register = Library()


# SGA Home Page


def index_sga(request):
    return render(request, 'index_sga.html', {})

# SGA Label Creator Page


def label_creator(request):
    return render(request, 'label_creator.html', {})


# SGA Label Information Page


def label_information(request):
    # Includes recipient search
    context = RecipientSize.objects.all()
    return render(request, 'label_information.html', {'recipients': context})


# SGA Label Template Page

def label_template(request):
    return render(request, 'label_template.html', {})


# SGA Label Customization Page

def label_customization(request):
    return render(request, 'label_customization.html', {})


# SGA Search sustance with autocomplete


def search_autocomplete_sustance(request):
    if request.is_ajax():
        q = request.GET.get('term', '')
        # Contains the typed characters, is valid since the first character
        # Search Parameter: Comercial Name or CAS Number
        if(any(c.isalpha() for c in q)):
            search_qs = Sustance.objects.filter(
                Q(comercial_name__icontains=q) | Q(synonymous__icontains=q))
        else:
            search_qs = Sustance.objects.filter(
                components__cas_number__icontains=q)
        results = []
        for r in search_qs:
            results.append({'label': r.comercial_name +
                            ' : '+r.synonymous, 'value': r.id})
        if(not results):
            results.append('No results')
        data = json.dumps(results)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)


def getSignalWord(request):
    signalWord = ''
    if request.is_ajax():
        ports = DangerIndication.objects.filter(
            sustance__in=[request.GET['substance_id']])
        for r in ports:
            if(signalWord == 'Peligro'):
                break
            else:
                if(r.warning_words == 'Sin palabra de advertencia' and signalWord == 'atención'):
                    break
                else:
                    # print(r.warning_words)
                    signalWord = r.warning_words
        data = signalWord
    else:
        data = 'fail'
    return HttpResponse(data)
