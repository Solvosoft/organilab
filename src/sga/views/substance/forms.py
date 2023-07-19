from django import forms
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.tagging import TaggingInput

from sga.models import Substance, SubstanceCharacteristics, DangerIndication, \
    WarningWord, PrudenceAdvice, SecurityLeaf, \
    ReviewSubstance
from sga.models import SubstanceObservation


class SustanceObjectForm(GTForm, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SustanceObjectForm, self).__init__(*args, **kwargs)
        self.fields['components_sga'].required = False

    class Meta:
        model = Substance
        fields = [
            'comercial_name', 'synonymous',
            'uipa_name', 'components_sga',
            'agrochemical', 'description',
            'brand', 'organization'
        ]
        widgets = {
            'comercial_name': genwidgets.TextInput,
            'uipa_name': genwidgets.TextInput,
            'synonymous': TaggingInput,
            'components_sga': genwidgets.SelectMultiple,
            'agrochemical': genwidgets.YesNoInput,
            'description': genwidgets.Textarea,
            'brand': genwidgets.TextInput,
            'organization': genwidgets.HiddenInput
        }


class SustanceCharacteristicsForm(GTForm, forms.ModelForm):
    class Meta:
        model = SubstanceCharacteristics
        exclude = ['substance', 'valid_molecular_formula', 'security_sheet']
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
            'number_index': genwidgets.TextInput,
            'number_ce': genwidgets.TextInput,
            'molecular_weight': genwidgets.TextInput,
            'concentration': genwidgets.TextInput
            # 'security_sheet': genwidgets.FileInput

        }


class DangerIndicationForm(GTForm, forms.ModelForm):

    def __init__(self, *arg, **kwargs):
        super(DangerIndicationForm, self).__init__(*arg, **kwargs)
        self.fields['warning_words'].required = False

    class Meta:
        model = DangerIndication
        fields = '__all__'
        widgets = {
            'code': genwidgets.TextInput,
            'description': genwidgets.Textarea,
            'warning_words': genwidgets.Select(),
            'warning_class': genwidgets.SelectMultiple(),
            'warning_category': genwidgets.SelectMultiple(),
            'prudence_advice': genwidgets.SelectMultiple()
        }


class WarningWordForm(GTForm, forms.ModelForm):
    class Meta:
        model = WarningWord
        fields = '__all__'
        widgets = {
            'name': genwidgets.TextInput,
            'weigth': genwidgets.NumberInput,
        }


class PrudenceAdviceForm(GTForm, forms.ModelForm):
    class Meta:
        model = PrudenceAdvice
        fields = '__all__'
        widgets = {
            'code': genwidgets.TextInput,
            'name': genwidgets.TextInput,
            'prudence_advice_help': genwidgets.Textarea,
        }


class ObservationForm(GTForm, forms.ModelForm):
    class Meta:
        model = SubstanceObservation
        fields = ['description']

        widgets = {
            'description': genwidgets.Textarea

        }


class SecurityLeafForm(forms.ModelForm, GTForm):

    def __init__(self, *arg, **kwargs):
        super(SecurityLeafForm, self).__init__(*arg, **kwargs)
        fields = self.fields
        for field in fields.keys():
            if field not in ['provider', 'substance']:
                self.fields[str(field)].widget = genwidgets.Textarea()
            if field in ['register_number', 'reach_number', 'reference']:
                self.fields[str(field)].widget = genwidgets.TextInput()

        self.fields['provider'].required = False
        self.fields['other_info'].label = _('Other Information')

    class Meta:
        model = SecurityLeaf
        exclude = ['substance']
        fields = "__all__"
        widgets = {
            'provider': genwidgets.Select
        }


class ReviewSubstanceForm(forms.ModelForm, GTForm):
    class Meta:
        model = ReviewSubstance
        fields = '__all__'
        widgets = {
            'substance': genwidgets.HiddenInput,
            'note': genwidgets.NumberInput,
            'is_approved': genwidgets.HiddenInput,
            'organization': genwidgets.HiddenInput,
            'created_by': genwidgets.HiddenInput
        }
