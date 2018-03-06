'''
Created on 4 may. 2017

@author: luis
'''
from django import template
from laboratory.forms import ObjectSearchForm
from django.shortcuts import get_object_or_404
from laboratory.utils import check_lab_group_has_perm,filter_laboratorist_technician
from laboratory.models import Laboratory

register = template.Library()




@register.simple_tag(takes_context=True)
def get_search_form(context):
    request = context['request']
    if 'q' in request.GET:
        form=ObjectSearchForm(request.GET)
    else:
        form=ObjectSearchForm()
    return form

# 
# @register.filter(name='has_group')
# def has_group(user, group_name):
#     return user.groups.filter(name=group_name).exists()


@register.simple_tag(takes_context=True)
def has_perms(context, codename):
    if 'request' in context:
        user = context['request'].user
        lab_pk = context['request'].session.get('lab_pk') 
        if user.has_perm(codename) :
            return True
        else:
            lab = get_object_or_404(Laboratory, pk=lab_pk)
            if check_lab_group_has_perm(user,lab,codename,filter_laboratorist_technician):
                return True
    return False

    
    
@register.simple_tag
def check_perms(*args, **kwargs):
    user= kwargs['user']
    perm= kwargs['perm']    
    return user.has_perm(perm)

