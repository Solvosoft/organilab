from async_notifications.utils import send_email_from_template
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from django.urls import reverse_lazy
from django.urls.base import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView

from authentication.forms import DemoRequestForm
from authentication.models import FeedbackEntry, DemoRequest


class PermissionDeniedView(TemplateView):
    template_name = 'laboratory/permission_denied.html'


class FeedbackView(CreateView):
    template_name = 'feedback/feedbackentry_form.html'
    model = FeedbackEntry
    fields = ['title', 'explanation', 'related_file']

    def get_success_url(self):
        text_message = _(
            'Thank you for your help. We will check your problem as soon as we can')
        messages.add_message(self.request, messages.SUCCESS, text_message)
        try:
            lab_pk = int(self.request.GET.get('lab_pk', 0))
        except:
            lab_pk = None
        dev = reverse('index')
        if self.request.user.is_authenticated:
            self.object.user = self.request.user
        if lab_pk:
            self.object.laboratory_id = lab_pk
            dev = reverse('laboratory:labindex', kwargs={'lab_pk': lab_pk})
        if self.request.user.is_authenticated or lab_pk:
            self.object.save()

        send_email_from_template("New feedback",
                                 settings.DEFAULT_FROM_EMAIL,
                                 context={
                                     'feedback': self.object
                                 },
                                 enqueued=True,
                                 user=None,
                                 upfile=self.object.related_file)

        return dev

def request_demo_done(request):
    return render(request, 'registration/request_demo_done.html')

from async_notifications.register import update_template_context
context = [
    ('data.name', 'name'),
    ('data.business_email', 'Business email'),
    ('data.company_name', 'Company name'),
    ('data.country', 'Country'),
    ('data.phone_number', 'Phone number'),
]
update_template_context("Request demo",  "New demo request", context,
                        message="""User information:<br>
                        {{data.name}}<br>
                        {{data.business_email}}<br>
                        {{data.company_name}}<br>
                        {{data.country}}<br>
                        {{data.phone_number}}
                        """)
class RequestDemoView(CreateView):
    model = DemoRequest
    form_class = DemoRequestForm
    template_name = 'registration/request_a_demo.html'
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        response = super().form_valid(form)
        send_email_from_template("Request demo",
                                 settings.DEFAULT_FROM_EMAIL,
                                 context={
                                     'data': form.cleaned_data
                                 },
                                 enqueued=True,
                                 user=None,
                                 upfile=None)
        messages.success(self.request, _('We will contact you soon'))
        return response