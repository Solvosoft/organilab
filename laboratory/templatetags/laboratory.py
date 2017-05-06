'''
Created on 4 may. 2017

@author: luis
'''
from django import template
from laboratory.utils import check_lab_perms
from laboratory.forms import ObjectSearchForm
register = template.Library()

from laboratory.models import Laboratory

@register.simple_tag(takes_context=True)
def has_laboratory_perm(context, perm):
    user = context['request'].user
    lab_pk = context['request'].session.get('lab_pk')
    lab = Laboratory.objects.filter(pk=lab_pk).first()
    if lab is not None:
        return check_lab_perms(lab, user, perm)
    
    return False

@register.simple_tag(takes_context=True)
def get_search_form(context):
    request = context['request']
    if 'q' in request.GET:
        form=ObjectSearchForm(request.GET)
    else:
        form=ObjectSearchForm()
    return form