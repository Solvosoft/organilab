from django import forms
from django.utils.translation import ugettext_lazy as _
from djgentelella.forms.forms import CustomForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.selects import AutocompleteSelect
from djgentelella.forms.forms import GTForm
from sga.models import Substance, RecipientSize, TemplateSGA, DangerIndication,DangerPrudence


class RecipientInformationForm(forms.Form):
    substance = forms.ModelChoiceField(queryset=Substance.objects.all())
    name = forms.CharField(max_length=150, required=True )
    phone = forms.CharField(max_length=15, required=True )
    address = forms.CharField(max_length=100, required=True )
    commercial_information = forms.Textarea( )
    recipients = forms.ModelChoiceField(queryset=RecipientSize.objects.all())
    templates = forms.ModelChoiceField(queryset=TemplateSGA.objects.all())

class SGAEditorForm(CustomForm,forms.ModelForm):
    class Meta:
        model = DangerPrudence
        fields = ('prudence_advice','danger_indication')
        widgets = {
            'prudence_advice':AutocompleteSelect('prudencesearch'),
            'danger_indication': AutocompleteSelect('dangersearch')
        }

class EditorForm(forms.ModelForm):
    preview = forms.CharField(widget=forms.HiddenInput())
    json_representation = forms.CharField(widget=forms.HiddenInput())
    class Meta:
        model = TemplateSGA
        fields = ('name', 'recipient_size', 'json_representation', 'community_share', 'preview')


class SearchDangerIndicationForm(CustomForm, forms.Form):

    codes = forms.ModelMultipleChoiceField(queryset=DangerIndication.objects.all().exclude(code="Ninguno"), widget=genwidgets.SelectMultiple, required=True)

class PersonalForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    json_representation = forms.CharField(widget=forms.HiddenInput()),
    sizes = forms.CharField(required=True, widget=genwidgets.NumberInput)

class DonateForm(GTForm, forms.Form):
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
