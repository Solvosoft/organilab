from django import forms
from .models import Laboratory
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from ajax_select.fields import AutoCompleteSelectMultipleField
from django.utils.translation import ugettext_lazy as _


class ObjectSearchForm(forms.Form):
    q = AutoCompleteSelectMultipleField(
        'objects', required=False, help_text=_("Search by name, code or CAS number"))
    all_labs = forms.BooleanField(
        widget=forms.CheckboxInput, required=False, label=_("All labs"))

    
class UserSearchForm(forms.Form):
    user = AutoCompleteSelectMultipleField(
        'users', required=False, help_text=_("Search by username, name or lastname"))
    action = forms.CharField(widget=forms.HiddenInput)


class UserCreate(UserCreationForm):
    first_name = forms.CharField(label=_('First name'))
    last_name = forms.CharField(label=_('Last name'))
    email = forms.EmailField(label=_('Email'))

    def save(self):
        user = super(UserCreate, self).save()
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.save()
        return user

class UserAccessForm(forms.Form):
    access = forms.BooleanField(widget=forms.CheckboxInput(
        attrs={'id': 'user_cb_'}))  # User_checkbox_id
    # For delete users. Add a delete button.

class LaboratoryCreate(forms.Form):
    name = forms.CharField(label=_('Name'))

    def save(self,user):
        lab = Laboratory()
        lab.name = self.cleaned_data['name']
        lab.save()
        lab.lab_admins.add(user)


#Traduccion (Multilenguaje)
# Validacion()
# Acomodar los imports
#Admins, Laboraristas, Estudiantes
