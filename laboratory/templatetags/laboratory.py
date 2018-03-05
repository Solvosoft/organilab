'''
Created on 4 may. 2017

@author: luis
'''
from django import template
from laboratory.utils import check_lab_perms
from laboratory.forms import ObjectSearchForm
register = template.Library()

from laboratory.models import Laboratory

# @register.simple_tag(takes_context=True)
# def has_laboratory_perm(context, perm):
#     if 'request' in context:
#         user = context['request'].user
#         lab_pk = context['request'].session.get('lab_pk')
#         lab = Laboratory.objects.filter(pk=lab_pk).first()
#         if lab is not None:
#             return check_lab_perms(lab, user, perm)
#     
#     return False

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
        return user.has_perm(codename)
    return False

    
    
@register.simple_tag
def check_perms(*args, **kwargs):
    user= kwargs['user']
    perm= kwargs['perm']    
    return user.has_perm(perm)

