from django import forms
from ajax_select.fields import AutoCompleteSelectMultipleField
from django.utils.translation import ugettext_lazy as _

class ObjectSearchForm(forms.Form):
    q = AutoCompleteSelectMultipleField('objects', required=False, help_text=_("Search by name, code or CAS number"))
    all_labs = forms.BooleanField(widget=forms.CheckboxInput, required=False, label="All labs")