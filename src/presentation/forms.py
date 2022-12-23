from django import forms
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.wysiwyg import TextareaWysiwyg
from djgentelella.widgets import core as djgenwidgets

from presentation.models import FeedbackEntry


class DonateForm(GTForm):
    name = forms.CharField(
        label=_('Name'), max_length=200, required=True,
        widget=genwidgets.TextInput)
    amount = forms.CharField(
        label=_('Amount'), required=True, widget=genwidgets.NumberInput,
        help_text=_("*Type the amount in dollars"))
    email = forms.CharField(
        label=_('Email'), required=True, widget=genwidgets.EmailMaskInput)
    is_donator = forms.BooleanField(
        label=_('Add me to the donators list'), widget=genwidgets.YesNoInput,
        initial=True)


class FeedbackEntryForm(forms.ModelForm, GTForm):
    class Meta:
        model = FeedbackEntry
        fields = ['title', 'explanation', 'related_file']
        widgets = {
            'title': djgenwidgets.TextInput,
            'explanation': TextareaWysiwyg,
             'related_file': djgenwidgets.FileInput

        }