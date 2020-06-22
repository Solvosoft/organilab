from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
# Create your views here.
from django.contrib.auth.models import User, Group
from django import forms
from django.core.exceptions import ValidationError
from laboratory.models import OrganizationStructure, Profile
from authentication.models import DemoRequest
from constance import config
from django.contrib.auth import authenticate, login
from django.urls.base import reverse_lazy, reverse
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.views.generic.base import TemplateView
from django.contrib import messages
from django.views.generic.edit import CreateView
from authentication.models import FeedbackEntry
from async_notifications.utils import send_email_from_template
from django.conf import settings
from djgentelella.forms.forms import CustomForm
from djgentelella.widgets import core as genwidgets
from django import forms
from django.core.mail import send_mail

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


def get_organization_admin_group():
    return Group.objects.get(pk=config.GROUP_ADMIN_PK)



def ask_demo_done(request):
    return render(request, 'registration/signup_done.html')

@require_POST
def demo(request):
    form = DemoRequestForm(request.POST)

    if form.is_valid():
        form.save(commit=True)
        html_content = '<h1>New Demo request</h1>'+ \
                '<p><label><b>Company Name: </b></label>'+form.cleaned_data['company_name']+'<br>'+ \
                '<label><b>Employee Name: </b></label>'+form.cleaned_data['first_name']+' '+form.cleaned_data['last_name']+'<br>'+ \
                '<label><b>Phone number: </b></label>'+form.cleaned_data['phone_number']+'<br>'+ \
                '<label><b>Country: </b></label>'+form.cleaned_data['country']+"</p><br><br><br>"+ \
                'Powered by Solvosoft\'s Team.'

        text_content = 'New Demo request \n'+ \
                'Company Name: '+form.cleaned_data['company_name']+'\n'+ \
                'Employee Name: '+form.cleaned_data['first_name']+' '+form.cleaned_data['last_name']+'\n'+ \
                'Phone number: '+form.cleaned_data['phone_number']+'\n'+ \
                'Country: '+form.cleaned_data['country']+"\n\n\n\n\n"+ \
                'Powered by Solvosoft\'s Team.'
        send_mail(
            'New Demo request Company: '+form.cleaned_data['company_name'],
            text_content,
            'from@localhost',
            ['to@localhost'],
            fail_silently=False,
            html_message=html_content
            )
        return redirect(reverse_lazy('ask_demo_done'))
    
    return render(request, 'registration/signup.html',
                    {'form_signup': form})


class OrgLoginView(LoginView):
    
    def get_context_data(self, **kwargs): 
        self.context = LoginView.get_context_data(self, **kwargs)
        return self.context


class DemoLoginView(LoginView):
    model = DemoRequest
    template_name = 'registration/signup.html'

    def get_context_data(self, **kwargs):
        self.context = LoginView.get_context_data(self, **kwargs)
        self.context['form_signup'] = DemoRequestForm()
        return self.context



class DemoRequestForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=120, required=True,)
    last_name = forms.CharField(
        max_length=120, required=True,)
    business_email = forms.CharField(
        max_length=70, required=True,)
    company_name = forms.CharField(
        max_length=120, required=True,)
    country = forms.CharField(
        max_length=120, required=True,)
    phone_number = forms.CharField(
        max_length=12, required=True,)

    
    class Meta:
        model = DemoRequest
        fields = ('first_name', 'last_name', 'business_email',
                  'company_name', 'country', 'phone_number')

