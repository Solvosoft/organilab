from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from django.core.urlresolvers import reverse
from django_ajax.decorators import ajax
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
import json
from laboratory.decorators import user_group_perms
from laboratory.registry import TOUR_STEPS_LAB_JSON, TOUR_STEPS_FURNITURE_JSON


@login_required
def lab_index(request, lab_pk):
    return render(request, 'laboratory/index.html',
                  {'laboratory': lab_pk})


@ajax
@login_required
def get_tour_steps(request):
    if request.method == 'GET' and request.is_ajax():
        tour = {
            'steps': TOUR_STEPS_LAB_JSON,
            'template': render_to_string('tour/tourtemplate.html', request=request)
        }
        return json.dumps(tour)
    return 0


@ajax
@login_required
def get_tour_steps_furniture(request):
    if request.method == 'GET' and request.is_ajax():
        tour = {
            'steps': TOUR_STEPS_FURNITURE_JSON,
            'template': render_to_string('tour/tourtemplate.html', request=request)
        }
        return json.dumps(tour)
    return 0

# def is_laboratory_admin(user):
#     return bool(user.groups.filter(name='laboratory_admin'))
#
# def is_laboratory_student(user):
#     return bool(user.groups.filter(name='laboratory_student'))
#
# def is_laboratory_teacher(user):
#     return bool(user.groups.filter(name='laboratory_teacher'))
