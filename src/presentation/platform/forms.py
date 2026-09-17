from django import forms
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets


class SystemParameterForm(GTForm, forms.Form):
    value = forms.CharField(
        required=False,
        label=_("Value"),
        help_text=_("Yes/No values: true or false. Dates: YYYY-MM-DD."),
        widget=genwidgets.TextInput,
    )
