from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.forms import UserCreationForm
# Create your views here.
from django.contrib.auth.models import User, Group
from django import forms
from django.core.exceptions import ValidationError
from laboratory.models import OrganizationStructure, Profile
from constance import config
from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget
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


class SignUpForm(CustomForm, UserCreationForm):
    ROLES = (
        (1, _('Organization administrator')),
        (2, _('Student'))
    )
    role = forms.ChoiceField(choices=ROLES, widget=genwidgets.RadioSelect())
    organization_name = forms.CharField(
        max_length=120, required=False, help_text=_('Your organization name'))

    captcha = ReCaptchaField(widget=ReCaptchaWidget())


    def clean(self):
        dev = super(SignUpForm, self).clean()
        if self.cleaned_data['role'] == '1':
            if not self.cleaned_data['organization_name']:
                raise ValidationError(
                    _('Organization name is required when role Organization administrator is selected'))

        return dev

    def save(self, commit=True):
        instance = UserCreationForm.save(self, commit=commit)
        group = get_organization_admin_group()
        org = OrganizationStructure(
            name=self.cleaned_data['organization_name'],
            group=group
        )
        org.save()
        pt = Profile(user=instance,
                     phone_number="8888-8888",
                     id_card="0-0000-0000",
                     organization=org
                     )
        pt.save()

        instance.groups.add(group)
        return instance

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name',
                  'email', 'password1', 'password2', )


@require_POST
def signup(request):
    form_login = AuthenticationForm()
    form = SignUpForm(request.POST)
    if form.is_valid():
        form.save()
        username = form.cleaned_data.get('username')
        raw_password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=raw_password)
        login(request, user)
        send_email_from_template("new user", user.email,
                                 context={
                                     'user': user,
                                     'role': form.cleaned_data['role'],
                                     'organization': form.cleaned_data['organization_name']
                                 },
                                 enqueued=True,
                                 user=user,
                                 upfile=None)
        return redirect(reverse_lazy('index'))
    # else:
    #    form = SignUpForm()
    return render(request, 'registration/login.html',
                  {'form_signup': form,
                   'form': form_login})


class OrgLoginView(LoginView):

    def get_context_data(self, **kwargs):
        self.context = LoginView.get_context_data(self, **kwargs)
        self.context['form_signup'] = SignUpForm()
        return self.context
