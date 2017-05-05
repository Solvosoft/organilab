'''
Created on 4 may. 2017

@author: luis
'''
from django import template
from laboratory.utils import check_lab_perms
register = template.Library()

from laboratory.models import Laboratory

@register.simple_tag(takes_context=True)
def has_laboratory_perm(context, perm):
    if 'request' in context:
        user = context['request'].user
        lab_pk = context['request'].session.get('lab_pk')
        lab = Laboratory.objects.filter(pk=lab_pk).first()
        if lab is not None:
            return check_lab_perms(lab, user, perm)
    
    return False