from django import forms
from djgentelella.forms.forms import GTForm

from djgentelella.widgets import core as genwidgets

from sga.models import Substance,SubstanceCharacteristics
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
