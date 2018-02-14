# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator
from django import forms

from laboratory.models import LaboratoryRoom, Laboratory, OrganizationStructure
from laboratory.decorators import check_lab_permissions, user_lab_perms

from .djgeneric import  ListView



class OrganizationSelectableForm(forms.Form):
    organizations = OrganizationStructure.objects.all()
    select = forms.ChoiceField(choices = organizations, label="", initial='', widget=forms.Select(), required=True)
    


@method_decorator(check_lab_permissions, name='dispatch')
@method_decorator(login_required, name='dispatch')
@method_decorator(user_lab_perms(perm='report'), name='dispatch')
class OrganizationReportView(ListView):
    model = OrganizationStructure
    template_name = "laboratory/report_organizationlaboratory_list.html"

    def get_queryset(self):
        form = OrganizationSelectableForm(self.request.GET)
        lab = get_object_or_404(Laboratory, pk=self.lab)
        return lab.rooms.all()
