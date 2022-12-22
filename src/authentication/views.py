from async_notifications.utils import send_email_from_template
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.urls.base import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auth_and_perms.api.serializers import AuthenticateDataRequestSerializer
from auth_and_perms.models import AuthenticateDataRequest
from authentication.forms import DemoRequestForm, FeedbackEntryForm
from authentication.models import FeedbackEntry, DemoRequest


class PermissionDeniedView(TemplateView):
    template_name = 'laboratory/permission_denied.html'


@method_decorator(login_required(), name='dispatch')
class FeedbackView(CreateView):
    template_name = 'feedback/feedbackentry_form.html'
    model = FeedbackEntry
    form_class = FeedbackEntryForm

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


class SignDataRequestViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        instance = AuthenticateDataRequest.objects.filter(id_transaction=request.data['data']['id_transaction']).first()
        if instance:
            data = request.data.get('data')
            if data:
                serializer = AuthenticateDataRequestSerializer(instance, data=data)
                if serializer.is_valid():
                    serializer.save()
            return Response({'data': True})
        return Response({'data': None})

#