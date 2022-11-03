from django import forms
from django.contrib.auth.models import User

from djgentelella.forms.forms import CustomForm
from djgentelella.widgets import core as djgenwidgets

from auth_and_perms.models import Rol
from authentication.models import DemoRequest
from captcha.fields import ReCaptchaField
from django.utils.translation import gettext_lazy as _


class DemoRequestForm(forms.ModelForm):
    captcha = ReCaptchaField()

    class Meta:
        model = DemoRequest
        fields = '__all__'


class CreateUserForm(CustomForm, forms.ModelForm):
    phone_number = forms.CharField(max_length=25, label=_('Phone'), widget=djgenwidgets.PhoneNumberMaskInput)
    id_card = forms.CharField(label=_('ID Card'), max_length=100, widget=djgenwidgets.TextInput)
    job_position = forms.CharField(label=_('Job Position'), max_length=100, widget=djgenwidgets.TextInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': djgenwidgets.TextInput,
            'first_name': djgenwidgets.TextInput,
            'last_name': djgenwidgets.TextInput,
            'email': djgenwidgets.EmailMaskInput
        }


class EditUserForm(CustomForm, forms.ModelForm):

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': djgenwidgets.TextInput,
            'first_name': djgenwidgets.TextInput,
            'last_name': djgenwidgets.TextInput,
            'email': djgenwidgets.EmailMaskInput
        }


class PasswordChangeForm(CustomForm, forms.Form):
    password = forms.CharField(widget=djgenwidgets.PasswordInput, required=True)
    password_confirm = forms.CharField(widget=djgenwidgets.PasswordInput, required=True)
