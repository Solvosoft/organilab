from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from laboratory.models import Rol
from djgentelella.widgets.selects import AutocompleteSelectMultipleBase

from djgentelella.forms.forms import CustomForm
from djgentelella.widgets import core as djgenwidgets
from authentication.models import DemoRequest
from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget
from django.utils.translation import ugettext_lazy as _


class DemoRequestForm(forms.ModelForm):
    captcha = ReCaptchaField(widget=ReCaptchaWidget())

    class Meta:
        model = DemoRequest
        fields = '__all__'


class CreateUserForm(CustomForm, forms.ModelForm):
    phone_number = forms.CharField(max_length=25, label=_('Phone'), widget=djgenwidgets.PhoneNumberMaskInput)
    id_card = forms.CharField(label=_('ID Card'), max_length=100, widget=djgenwidgets.TextInput)
    job_position = forms.CharField(label=_('Job Position'), max_length=100, widget=djgenwidgets.TextInput)
    rol = forms.ModelMultipleChoiceField(queryset=Rol.objects.all(), required=False, widget=djgenwidgets.SelectMultiple,
                                         label=_('Roles'))

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
