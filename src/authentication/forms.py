from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as djgenwidgets
from django.core.exceptions import ValidationError


class CreateUserForm(forms.ModelForm, GTForm):
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


class EditUserForm(forms.ModelForm, GTForm):

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': djgenwidgets.TextInput,
            'first_name': djgenwidgets.TextInput,
            'last_name': djgenwidgets.TextInput,
            'email': djgenwidgets.EmailMaskInput
        }


class PasswordChangeForm(GTForm, forms.Form):
    password = forms.CharField(widget=djgenwidgets.PasswordInput, max_length=128,
                               required=True, label=_('Password'))
    password_confirm = forms.CharField(widget=djgenwidgets.PasswordInput,
                                       max_length=128, required=True,
                                       label=_('Confirm Password'))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_password_confirm(self):
        password = self.cleaned_data.get("password")
        password_confirm = self.cleaned_data.get("password_confirm")
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError(_("The two password fields didn’t match."),
                    code="password_mismatch",
                )
        password_validation.validate_password(password_confirm, user=self.user)
        return password_confirm


