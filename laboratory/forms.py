from django import forms
from .models import Laboratory
from django.contrib.auth.models import User

from ajax_select.fields import AutoCompleteSelectMultipleField
from django.utils.translation import ugettext_lazy as _

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

class UserAccessForm(forms.Form):
    access = forms.BooleanField(widget = forms.CheckboxInput(attrs={'id':'user_cb_'})) #User_checkbox_id
    #For delete users. Add a delete button.


#Traduccion (Multilenguaje)
#Validacion()
#Acomodar los imports
#Admins, Laboraristas, Estudiantes
