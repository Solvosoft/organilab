from django import forms
from .models import Laboratory
from django.contrib.auth.models import User

from ajax_select.fields import AutoCompleteSelectMultipleField
from django.utils.translation import ugettext_lazy as _

from django.core import validators

class ObjectSearchForm(forms.Form):
    q = AutoCompleteSelectMultipleField('objects', required=False, help_text=_("Search by name, code or CAS number"))
    all_labs = forms.BooleanField(widget=forms.CheckboxInput, required=False, label="All labs")

class UserSearchForm(forms.Form):
    user = AutoCompleteSelectMultipleField('users', required = False, help_text = ("Search by username, name or lastname"))

class UserCreate(forms.Form):
    username = forms.CharField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    password = forms.CharField(widget = forms.PasswordInput)
    password_verification = forms.CharField(widget=forms.PasswordInput)

    def clean_password_verification(self):
        password = self.cleaned_data.get("password")
        password_verification = self.cleaned_data.get("password_verification")
        if password and password_verification and password != password_verification:
            raise forms.ValidationError(
                "Passwords don't match.",code='password_mismatch',
            )
        return password_verification

    """def clean(self):
        form_data = self.cleaned_data
        if form_data['password'] != form_data['password_verification']:
            self._errors["password"] = ["Password do not match"] # Will raise a error message
            del form_data['password']
        return form_data"""

    def save(self):
        username = self.cleaned_data['username']
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']

        user = User.objects.create(username=username,first_name=first_name, last_name=last_name, email=email, password=password)
        user.save()

class UserAccessForm(forms.Form):
    access = forms.BooleanField(widget = forms.CheckboxInput(attrs={'id':'user_cb_'})) #User_checkbox_id
    #For delete users. Add a delete button.


#Traduccion (Multilenguaje)
#Validacion()
#Acomodar los imports
#Admins, Laboraristas, Estudiantes
