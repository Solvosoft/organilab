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
from mptt.forms import TreeNodeChoiceField
from django.utils.functional import lazy

from laboratory.models import LaboratoryRoom, Laboratory, OrganizationStructure, PrincipalTechnician
from laboratory.decorators import check_lab_permissions, user_lab_perms

from .djgeneric import  ListView





class OrganizationSelectableForm(forms.Form):
    technician= None
    organizations = OrganizationStructure.objects.all() 
    filter_organization= TreeNodeChoiceField(queryset=organizations)

    
    def __init__(self, *args, **kwargs):
        #user =kwargs.pop('user_id',None)# user was passed to a single form

        super(OrganizationSelectableForm, self).__init__(*args, **kwargs)
        technician=PrincipalTechnician.objects.filter(credentials=None)
        if self.technician :
            organizations = OrganizationStructure.objects.get(pk=self.technician.organization.pk).get_descendants(include_self=True)
            self.fields['filter_organization'].queryset = organizations
            
        
 


@method_decorator(check_lab_permissions, name='dispatch')
@method_decorator(login_required, name='dispatch')
@method_decorator(user_lab_perms(perm='report'), name='dispatch')
class OrganizationReportView(ListView):
    model = Laboratory
    template_name = "laboratory/report_organizationlaboratory_list.html"
    organization = None

    def get_context_data(self, **kwargs):
        context = super(OrganizationReportView,self).get_context_data(**kwargs)
        
        context['form']  = self.form 
        
        if self.organization :
            organizations_child = OrganizationStructure.objects.get(pk=self.organization.pk).get_descendants(include_self=True)
            labs=Laboratory.objects.filter(organization__in=organizations_child)
            context['object_list'] = labs
            context['filter_organization']  = self.organization
           
            
        return context

     
    def get(self, request, *args, **kwargs):
        self.form = OrganizationSelectableForm(self.request.GET or None)
        return super(OrganizationReportView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):     
        self.form = OrganizationSelectableForm(self.request.POST or None)
        
        if self.form.is_valid():
            self.organization = self.form.cleaned_data['filter_organization']       

    
        return super(OrganizationReportView, self).get(request, *args, **kwargs)
    
    
    
