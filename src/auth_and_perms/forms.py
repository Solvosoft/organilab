from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets.selects import AutocompleteSelectMultiple

from auth_and_perms.models import Rol


class AddUserForm(GTForm, forms.Form):
    users = forms.ModelMultipleChoiceField(queryset=User.objects.all(), label=_("Users"),
        widget=AutocompleteSelectMultiple('userbase', attrs={'data-dropdownparent': '#addusermodal'}))


class AddProfileRolForm(GTForm, forms.Form):
    rols = forms.ModelMultipleChoiceField(queryset=Rol.objects.none(), label=_("Rols"),
                                          widget=AutocompleteSelectMultiple('rolbase'), required=True)
    contentobj_pk = forms.CharField(widget=forms.HiddenInput(), required=False)
    contentobj_pk = forms.CharField(widget=forms.HiddenInput(), required=False)
    org_pk = forms.CharField(widget=forms.HiddenInput(), required=True)