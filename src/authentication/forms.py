from django import forms
from django.contrib.auth.models import User
from djgentelella.forms.forms import CustomForm
from djgentelella.widgets import core as djgenwidgets

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