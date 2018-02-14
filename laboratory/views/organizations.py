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

from django.utils.functional import lazy

from laboratory.models import LaboratoryRoom, Laboratory, OrganizationStructure
from laboratory.decorators import check_lab_permissions, user_lab_perms

from .djgeneric import  ListView



class OrganizationSelectableForm(forms.Form):
    organizations = OrganizationStructure.objects.all()
    filter_organization = forms.ChoiceField(choices = [(o.id, str(o)) for o in organizations], label="Organization", initial='', widget=forms.Select(), required=True)
    
    
    def get(self, request, *args, **kwargs):
        return super(OrganizationSelectableForm, self).get(request, *args, **kwargs)
#     def __init__(self, *args, **kwargs):
#         if kwargs.get('user'):
#             self.user = kwargs.pop('user', None)


@method_decorator(check_lab_permissions, name='dispatch')
@method_decorator(login_required, name='dispatch')
@method_decorator(user_lab_perms(perm='report'), name='dispatch')
class OrganizationReportView(ListView):
    model = OrganizationStructure
    template_name = "laboratory/report_organizationlaboratory_list.html"


    def get_context_data(self, **kwargs):
         context = super(OrganizationReportView,self).get_context_data(**kwargs)
         lab = get_object_or_404(Laboratory, pk=self.lab)
         context['form']  = self.form 
#         context['object_list'] = lab.rooms.all()
#         context['laboratory'] = self.lab
         return context
     
# 
#     def get_form_kwargs(self):
#         kwargs = super(OrganizationReportView, self).get_form_kwargs() #put your view name in the super
#         user = self.request.user
# 
#         if user:
#             kwargs['user'] = user
# 
#         return kwargs
#     
     
    def get(self, request, *args, **kwargs):
        self.form = OrganizationSelectableForm(self.request.GET or None,)
        return super(OrganizationReportView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.form = OrganizationSelectableForm(self.request.POST or None)
        
        return super(OrganizationReportView, self).get(request, *args, **kwargs)
    
    
    
