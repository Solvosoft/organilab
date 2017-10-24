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

from laboratory.models import FeedbackEntry
from laboratory.decorators import check_lab_permissions
from laboratory.registry import TOUR_STEPS_JSON


@check_lab_permissions()
def index(request, lab_pk=None):
    if lab_pk is None:
        return redirect('laboratory:select_lab')
    return render(request, 'laboratory/index.html',
                  {'laboratory': lab_pk})


class PermissionDeniedView(TemplateView):
    template_name = 'laboratory/permission_denied.html'


class FeedbackView(CreateView):
    model = FeedbackEntry
    fields = '__all__'

    def get_success_url(self):
        text_message = _('Thank you for your help. We are gonna check your problem as soon as we can')
        messages.add_message(self.request, messages.SUCCESS, text_message)
        lab_pk = self.request.session.get('lab_pk')
        if lab_pk is not None:
            return reverse('laboratory:index', kwargs={'lab_pk': lab_pk})
        return reverse('laboratory:index')


@ajax
@login_required
def get_tour_steps(request):
    if request.method == 'GET' and request.is_ajax():
        tour = {
            'steps' : TOUR_STEPS_JSON,
            'template' :render_to_string('tour/tourtemplate.html', request=request)
        }
        return json.dumps(tour)
    return 0

def is_laboratory_admin(user):
    return bool(user.groups.filter(name='laboratory_admin'))

def is_laboratory_student(user):
    return bool(user.groups.filter(name='laboratory_student'))

def is_laboratory_teacher(user):
    return bool(user.groups.filter(name='laboratory_teacher'))
