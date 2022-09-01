from django import forms
from djgentelella.forms.forms import GTForm

from academic.models import SubstanceSGA, SustanceCharacteristicsSGA
from djgentelella.widgets import core as genwidgets


class SustanceObjectForm(GTForm, forms.ModelForm):
    class Meta:
        model = SubstanceSGA
        fields = [
            'comercial_name', 'synonymous',
            'uipa_name', 'components',
            'agrochemical', 'is_public',
            'description',
        ]
        widgets = {
            'comercial_name': genwidgets.TextInput,
            'uipa_name': genwidgets.TextInput,
            'components': genwidgets.SelectMultiple,
            'synonymous': genwidgets.TextInput,
            'is_public': genwidgets.YesNoInput,
            'agrochemical': genwidgets.YesNoInput,
            'description': genwidgets.Textarea,
        }

class SustanceCharacteristicsForm(GTForm, forms.ModelForm):
    class Meta:
        model = SustanceCharacteristicsSGA
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
