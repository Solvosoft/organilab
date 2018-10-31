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
from .models import Sustance, Component, RecipientSize, DangerIndication, PrudenceAdvice,Pictogram
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
    recipients= RecipientSize.objects.all()
    return render(request, 'label_creator.html', {'recipients': recipients,
'laboratory': 1
})


# SGA Label Information Page


def label_information(request):
    # Includes recipient search
    context = RecipientSize.objects.all()
    return render(request, 'label_information.html', {'recipients': context})


# SGA Label Template Page

def label_template(request):
    recipients= RecipientSize.objects.all()

    return render(request, 'label_template.html', {'recipients': recipients,
'laboratory': None
})


# SGA Label Editor Page

def label_editor(request):
    return render(request, 'label_editor.html', {})


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

# SGA Obtain substance information


def getSubstanceInformation(request):
    substanceInformation = {}
    signalWordSubstance = ''
    dangerIndicationsDescriptionSubstance = []
    dangerIndicationsCodeSubstance = []
    prudenceAdvicesNameSubstance = []
    prudenceAdvicesCodeSubstance = []
    pictogramasNameSubstance = []
    if request.is_ajax():
        dangerIndications = DangerIndication.objects.filter(sustance__in=request.GET['substance_id'])
        # ---------------------------------------------------------------------
        # ----------------------------Signal Word------------------------------
        for dangerIndication in dangerIndications:
            # Set priority to Danger
            if(str(signalWordSubstance) == 'Peligro'):
                break
            else:
                # Set priority to Warning
                if(str(dangerIndication.warning_words) == 'Sin palabra de advertencia' and str(signalWordSubstance) == 'atención'):
                    pass
                else:
                    signalWordSubstance = dangerIndication.warning_words
        substanceInformation['signalWord'] = str(signalWordSubstance)
        # ---------------------------------------------------------------------
        # --------------------------Danger Indications-------------------------
        for dangerIndication in dangerIndications:
            if (str(dangerIndication.code) in dangerIndicationsCodeSubstance):
                pass
            # Special cases
            # H410 > H400
            elif ('H410' in dangerIndicationsCodeSubstance and str(dangerIndication.code) == 'H400'):
                pass
            elif ('H400' in dangerIndicationsCodeSubstance and str(dangerIndication.code) == 'H410'):
                index = dangerIndicationsCodeSubstance.index('H400')
                dangerIndicationsCodeSubstance.pop(index)
                dangerIndicationsDescriptionSubstance.pop(index)
                dangerIndicationsDescriptionSubstance.append(str(dangerIndication.description))
                dangerIndicationsCodeSubstance.append(str(dangerIndication.code))
            # H411 > H401
            elif ('H411' in dangerIndicationsCodeSubstance and str(dangerIndication.code) == 'H401'):
                pass
            elif ('H401' in dangerIndicationsCodeSubstance and str(dangerIndication.code) == 'H411'):
                index = dangerIndicationsCodeSubstance.index('H401')
                dangerIndicationsCodeSubstance.pop(index)
                dangerIndicationsDescriptionSubstance.pop(index)
                dangerIndicationsDescriptionSubstance.append(str(dangerIndication.description))
                dangerIndicationsCodeSubstance.append(str(dangerIndication.code))
            # H412 > H402
            elif ('H412' in dangerIndicationsCodeSubstance and str(dangerIndication.code) == 'H402'):
                pass
            elif ('H402' in dangerIndicationsCodeSubstance and str(dangerIndication.code) == 'H412'):
                index = dangerIndicationsCodeSubstance.index('H402')
                dangerIndicatfionsCodeSubstance.pop(index)
                dangerIndicationsDescriptionSubstance.pop(index)
                dangerIndicationsDescriptionSubstance.append(str(dangerIndication.description))
                dangerIndicationsCodeSubstance.append(str(dangerIndication.code))
            # H314 > H318
            elif ('H314' in dangerIndicationsCodeSubstance and str(dangerIndication.code) == 'H318'):
                pass
            elif ('H318' in dangerIndicationsCodeSubstance and str(dangerIndication.code) == 'H314'):
                index = dangerIndicationsCodeSubstance.index('H318')
                dangerIndicationsCodeSubstance.pop(index)
                dangerIndicationsDescriptionSubstance.pop(index)
                dangerIndicationsDescriptionSubstance.append(str(dangerIndication.description))
                dangerIndicationsCodeSubstance.append(str(dangerIndication.code))
            else:
                dangerIndicationsDescriptionSubstance.append(str(dangerIndication.description))
                dangerIndicationsCodeSubstance.append(str(dangerIndication.code))
        substanceInformation['DangerIndications'] = dangerIndicationsDescriptionSubstance
        # ---------------------------------------------------------------------
        # ------------------Prudence Advices and Pictograms--------------------
        for dangerIndicationCode in dangerIndicationsCodeSubstance:
            prudenceAdvices = PrudenceAdvice.objects.filter(dangerindication=dangerIndicationCode)
            pictograms= Pictogram.objects.filter(dangerindication=dangerIndicationCode)
            if(prudenceAdvices):
                for prudenceAdvice in prudenceAdvices:
                    if (str(prudenceAdvice.code) in prudenceAdvicesCodeSubstance):
                        pass
                    else:
                        prudenceAdvicesNameSubstance.append(str(prudenceAdvice.name))
                        dangerIndicationsCodeSubstance.append(str(prudenceAdvice.code))
            if(pictograms):
                for pictogram in pictograms:
                    if (str(pictogram.name) in pictogramasNameSubstance):
                        pass
                    else:
                        if(str(pictogram.name) != 'Sin Pictograma'):
                            pictogramasNameSubstance.append(str(pictogram.name))
        substanceInformation['PrudenceAdvices'] = prudenceAdvicesNameSubstance
        substanceInformation['Pictograms'] = pictogramasNameSubstance
        # ---------------------------------------------------------------------
        # print(substanceInformation)
        data = json.dumps(substanceInformation)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)
