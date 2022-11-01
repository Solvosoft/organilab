from django import forms
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets

from laboratory.models import OrganizationUserManagement


class AddUserForm(forms.ModelForm, GTForm):
    class Meta:
        model = OrganizationUserManagement
        fields = ['users']
        widgets = {
            'users': genwidgets.SelectMultiple(attrs={'data-dropdownparent': '#addusermodal'})
        }