from django import forms
from django.contrib.auth.models import User
from djgentelella.forms.forms import CustomForm
from djgentelella.widgets import core as djgenwidgets
from authentication.models import DemoRequest
from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget

class DemoRequestForm(forms.ModelForm):
    captcha = ReCaptchaField(widget=ReCaptchaWidget())

    class Meta:
        model = DemoRequest
        fields = '__all__'

class CreateUserForm(CustomForm, forms.ModelForm):

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': djgenwidgets.TextInput,
            'first_name': djgenwidgets.TextInput,
            'last_name': djgenwidgets.TextInput,
            'email': djgenwidgets.EmailMaskInput
        }
