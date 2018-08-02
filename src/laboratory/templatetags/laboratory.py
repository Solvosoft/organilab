'''
Created on 4 may. 2017

@author: luis
'''
from django import template
from laboratory.forms import ObjectSearchForm
from django.shortcuts import get_object_or_404
from laboratory.utils import check_lab_group_has_perm, filter_laboratorist_technician,\
    get_user_laboratories
from laboratory.models import Laboratory

register = template.Library()


@register.simple_tag(takes_context=True)
def get_search_form(context):
    request = context['request']
    if 'q' in request.GET:
        form = ObjectSearchForm(request.GET)
    else:
        form = ObjectSearchForm()
    return form


@register.simple_tag(takes_context=True)
def has_perms(context, codename, lab_pk=None):
    if 'request' in context:
        user = context['request'].user
        if 'laboratory' in context:
            lab_pk=context['laboratory']
            lab = get_object_or_404(Laboratory, pk=lab_pk)
            if check_lab_group_has_perm(
                    user, lab, codename,
                    filter_laboratorist_technician):
                return True
        elif user.has_perm(codename):
            return True
        
    return False


@register.simple_tag
def check_perms(*args, **kwargs):
    user = kwargs['user']
    perm = kwargs['perm']
    return user.has_perm(perm)


@register.simple_tag(takes_context=True)
def get_user_labs(context):
    if 'request' not in context:
        return []

    return get_user_laboratories(context['request'].user)
