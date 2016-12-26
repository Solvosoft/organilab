from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView


def index(request, lab_pk=None):
    if lab_pk is None:
        return redirect('laboratory:select_lab')
    return render(request, 'laboratory/index.html',
                  {'laboratory': lab_pk})


class PermissionDeniedView(TemplateView):
    template_name = 'laboratory/permission_denied.html'
