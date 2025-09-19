from django import forms
from djgentelella.forms.forms import GTForm
from djgentelella.widgets.files import FileChunkedUpload

from laboratory.models import Object, SustanceCharacteristics, Laboratory
from djgentelella.widgets import core as genwidgets


class SustanceObjectForm(GTForm, forms.ModelForm):

    class Meta:
        model = Object
        fields = [
            "name",
            "synonym",
            "code",
            "is_public",
            "description",
            "model",
            "serie",
            "plaque",
            "features",
        ]
        widgets = {
            "name": genwidgets.TextInput,
            "synonym": genwidgets.TextInput,
            "code": genwidgets.TextInput,
            "is_public": genwidgets.YesNoInput,
            "description": genwidgets.Textarea,
            "model": genwidgets.TextInput,
            "serie": genwidgets.TextInput,
            "plaque": genwidgets.TextInput,
            "features": genwidgets.SelectMultiple,
        }


class SustanceCharacteristicsForm(GTForm, forms.ModelForm):
    class Meta:
        model = SustanceCharacteristics
        exclude = ["obj", "valid_molecular_formula"]
        widgets = {
            "iarc": genwidgets.Select,
            "imdg": genwidgets.Select,
            "white_organ": genwidgets.SelectMultiple,
            "bioaccumulable": genwidgets.YesNoInput,
            "molecular_formula": genwidgets.TextInput,
            "cas_id_number": genwidgets.TextInput,
            "is_precursor": genwidgets.YesNoInput,
            "precursor_type": genwidgets.Select,
            "h_code": genwidgets.SelectMultiple,
            "ue_code": genwidgets.SelectMultiple,
            "nfpa": genwidgets.SelectMultiple,
            "storage_class": genwidgets.SelectMultiple,
            "seveso_list": genwidgets.YesNoInput,
            "img_representation": FileChunkedUpload,
            # 'security_sheet': genwidgets.FileInput
        }
