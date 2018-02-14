'''
Created on 14 feb. 2018

@author: miguel
'''
from django.contrib.auth.models import User
from django import template
from laboratory.utils import check_lab_perms
from laboratory.forms import ObjectSearchForm
register = template.Library()


from laboratory.models import (OrganizationStructure, 
                               PrincipalTechnician, 
                               ) 


@register.simple_tag(takes_context=True)
def get_selectable_organizations(context):   
    organizations = OrganizationStructure.objects.all()
    return organizations
