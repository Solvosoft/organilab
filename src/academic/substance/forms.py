from django import forms
from djgentelella.forms.forms import GTForm

from djgentelella.widgets import core as genwidgets

from academic.models import SubstanceObservation
from sga.models import Substance, SubstanceCharacteristics, DangerIndication, WarningWord, PrudenceAdvice
from djgentelella.widgets.tagging import TaggingInput

class SustanceObjectForm(GTForm, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(SustanceObjectForm,self).__init__(*args, **kwargs)
        self.fields['components_sga'].required = False

    class Meta:
        model = Substance
        fields = [
            'comercial_name', 'synonymous',
            'uipa_name', 'components_sga',
            'agrochemical', 'description',
        ]
        widgets = {
            'comercial_name': genwidgets.TextInput,
            'uipa_name': genwidgets.TextInput,
            'synonymous': TaggingInput,
            'components_sga': genwidgets.SelectMultiple,
            'agrochemical': genwidgets.YesNoInput,
            'description': genwidgets.Textarea,
        }

class SustanceCharacteristicsForm(GTForm, forms.ModelForm):
    class Meta:
        model = SubstanceCharacteristics
        exclude = ['substance', 'valid_molecular_formula','security_sheet']
        widgets = {
            'iarc': genwidgets.Select,
            'imdg': genwidgets.Select,
            'white_organ': genwidgets.SelectMultiple,
            'bioaccumulable': genwidgets.YesNoInput,
            'molecular_formula': genwidgets.TextInput,
            'cas_id_number': genwidgets.TextInput,
            'is_precursor': genwidgets.YesNoInput,
            'precursor_type': genwidgets.Select,
            'h_code': genwidgets.SelectMultiple,
            'ue_code': genwidgets.SelectMultiple,
            'nfpa': genwidgets.SelectMultiple,
            'storage_class': genwidgets.SelectMultiple,
            'seveso_list': genwidgets.YesNoInput,
            # 'security_sheet': genwidgets.FileInput

        }

class DangerIndicationForm(GTForm,forms.ModelForm):

    def __init__(self, *arg, **kwargs):
        super(DangerIndicationForm, self).__init__(*arg,**kwargs)
        self.fields['pictograms'].required=False
        self.fields['warning_words'].required=False

    class Meta:
        model = DangerIndication
        exclude = ['organilab_context']
        widgets = {
            'code' : genwidgets.TextInput,
            'description' : genwidgets.Textarea,
            'warning_words' : genwidgets.Select(),
            'pictograms' : genwidgets.SelectMultiple(),
            'warning_class': genwidgets.SelectMultiple(),
            'warning_category' : genwidgets.SelectMultiple(),
            'prudence_advice' : genwidgets.SelectMultiple()
        }
class WarningWordForm(GTForm,forms.ModelForm):

    class Meta:
        model = WarningWord
        exclude = ['organilab_context']
        widgets = {
            'name' : genwidgets.TextInput,
            'weigth' : genwidgets.NumberInput,
        }
class PrudenceAdviceForm(GTForm,forms.ModelForm):

    class Meta:
        model = PrudenceAdvice
        exclude = ['organilab_context']
        widgets = {
            'code' : genwidgets.TextInput,
            'name' : genwidgets.TextInput,
            'prudence_advice_help' : genwidgets.Textarea,
        }


class ObservacionForm(GTForm, forms.ModelForm):

    class Meta:
        model = SubstanceObservation
        fields = ['description']

        widgets = {
            'description': genwidgets.Textarea

        }
