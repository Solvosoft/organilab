from django import forms
from djgentelella.forms.forms import GTForm
from djgentelella.widgets.selects import AutocompleteSelectMultiple
from django.utils.translation import gettext_lazy as _
from laboratory.models import OrganizationUserManagement


class AddUserForm(forms.ModelForm, GTForm):
    class Meta:
        model = OrganizationUserManagement
        fields = ['users']
        widgets = {
            'users': AutocompleteSelectMultiple('userbase', attrs={'data-dropdownparent': '#addusermodal'})
        }
        labels = {
            'users': _("Users")
        }