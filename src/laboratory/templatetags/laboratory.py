'''
Created on 4 may. 2017

@author: luis
'''
from django import template

from academic.models import ProcedureStep, ProcedureRequiredObject
from laboratory.forms import ObjectSearchForm
from django.shortcuts import get_object_or_404
from laboratory.utils import check_lab_group_has_perm, filter_laboratorist_profile, \
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

        if user.has_perm(codename) or user.is_superuser:
            return True
        else:
            lab_pk = context['request'].resolver_match.kwargs.get('lab_pk', None)

            # Permit to redirect User to select form
            if not lab_pk:
                return False
            lab = get_object_or_404(Laboratory, pk=lab_pk)
            if check_lab_group_has_perm(
                    user, lab, codename,
                    filter_laboratorist_profile):
                return True

    return False


@register.simple_tag(takes_context=True)
def index_permissions(context):
    dev = {
        'view_laboratory': has_perms(context, "laboratory.view_laboratory"),
        'view_procedure': has_perms(context, "academic.view_procedure"),
        'delete_laboratory': has_perms(context, "laboratory.delete_laboratory"),
        'add_laboratory': has_perms(context, "laboratory.add_laboratory"),
        'manage_laboratory': has_perms(context, "laboratory.change_laboratory"),
        'add_furniture': has_perms(context, "laboratory.add_furniture"),
        'add_object': has_perms(context, "laboratory.add_object"),
        "add_features": has_perms(context, "laboratory.add_objectfeatures"),
        'view_reports': has_perms(context, "laboratory.view_report"),
        'do_reports': has_perms(context, "laboratory.do_report"),
        'add_reservation': has_perms(context, "djreservation.add_reservation"),
        'view_organizationstructure': has_perms(context, "laboratory.view_organizationstructure"),
        'add_reservations': has_perms(context, "reservations_management.add_reservation"),
        'add_reserved_product': has_perms(context, "reservations_management.add_reserved_product"),
        'delete_reserved_product': has_perms(context, "reservations_management.delete_reserved_product"),
    }

    dev['show_labview'] = dev['view_laboratory'] or dev['view_procedure']
    dev['admin_lab'] = dev['add_laboratory'] or dev['manage_laboratory'] \
                       or dev['add_furniture'] or dev['add_object'] \
                       or dev["add_features"]

    dev['show_reports'] = dev['view_reports'] or dev['do_reports']

    return dev


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


@register.simple_tag(takes_context=True)
def show_laboratory_name(context):
    if 'laboratory' in context and context['laboratory']:
        lab = Laboratory.objects.filter(pk=context['laboratory']).first()
        if lab:
            return str(lab)
    return ''

@register.filter()
def to_int(value):
   return int(value)

@register.filter()
def get_lab_pk(value):
    if isinstance(value, str):
        if len(value)==0:
            return 0
        else:
            return value
    elif isinstance(value, int):
        return value


@register.simple_tag()
def show_reserve_button(procedure):
    show_reserve_btn = False
    steps = list(ProcedureStep.objects.filter(procedure=procedure))
    items = ProcedureRequiredObject.objects.filter(step__in=steps)
    if items.exists():
        show_reserve_btn = True
    return show_reserve_btn