from django import forms
from ajax_select.fields import AutoCompleteSelectMultipleField
from django.utils.translation import ugettext_lazy as _

class ObjectSearchForm(forms.Form):
    q = AutoCompleteSelectMultipleField('objects', required=False, help_text=_("Search by name, code or CAS number"))
    all_labs = forms.BooleanField(widget=forms.CheckboxInput, required=False, label="All labs")

class UserSearchForm(forms.Form):
    user = AutoCompleteSelectMultipleField('users', help_text=_("Find_users"))

class UserCreate(forms.Form):
    username = forms.CharField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    password = forms.CharField(widget = forms.PasswordInput)
    password_verification = forms.CharField(widget=forms.PasswordInput)

#Traduccion (Multilenguaje)
#Validacion()
#Acomodar los imports
#Admins, Laboraristas, Estudiantes
