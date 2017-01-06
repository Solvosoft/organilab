from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from django.core.urlresolvers import reverse
from laboratory.models import FeedbackEntry


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
        lab_pk = self.request.session.get('lab_pk')
        if lab_pk is not None:
            return reverse('laboratory:index', kwargs={'lab_pk': lab_pk})
        return reverse('laboratory:index')
