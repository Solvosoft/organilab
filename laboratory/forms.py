from django import forms
from ajax_select.fields import AutoCompleteSelectMultipleField

class ObjectSearchForm(forms.Form):
    q = AutoCompleteSelectMultipleField('objects', required=False)
    all_labs = forms.BooleanField(widget=forms.CheckboxInput, required=False, label="All labs")