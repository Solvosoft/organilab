from ajax_select.fields import AutoCompleteSelectField
from django import forms
from django.utils.translation import ugettext_lazy as _
from djgentelella.forms.forms import CustomForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.selects import AutocompleteSelect

from sga.models import WarningWord, Substance, RecipientSize, TemplateSGA, DangerIndication

class RecipientInformationForm(forms.Form):
    substance = forms.ModelChoiceField(queryset=Substance.objects.all())
    name = forms.CharField(max_length=150, required=True )
    phone = forms.CharField(max_length=15, required=True )
    address = forms.CharField(max_length=100, required=True )
    commercial_information = forms.Textarea( )
    recipients = forms.ModelChoiceField(queryset=RecipientSize.objects.all())


class SGAEditorForm(forms.Form):
    #warningwords = forms.ModelChoiceField(queryset=WarningWord.objects.all(),
     #                                     label=_("Warning Word"))
    dangerindication = AutocompleteSelect('dangerbasename')
    #,
                        #                  label=_("Danger Indication"))
    prudenceadvice = AutoCompleteSelectField('prudenceadvices',
                                          label=_("Prudence Advices"))


class EditorForm(forms.ModelForm):
    preview = forms.CharField(widget=forms.HiddenInput())
    json_representation = forms.CharField(widget=forms.HiddenInput())
    class Meta:
        model = TemplateSGA
        fields = ('name', 'recipient_size', 'json_representation', 'community_share', 'preview')


class SearchDangerIndicationForm(CustomForm, forms.Form):

    codes = forms.ModelMultipleChoiceField(queryset=DangerIndication.objects.all().exclude(code="Ninguno"), widget=genwidgets.SelectMultiple, required=True)