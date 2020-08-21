from django import forms

from laboratory.models import Object, SustanceCharacteristics


class SustanceObjectForm(forms.ModelForm):
    class Meta:
        model = Object
        fields = [
            'name', 'synonym',
            'code', 'is_public',
            'description',
            'model', 'serie', 'plaque', 'laboratory', 'features'
        ]

class SustanceCharacteristicsForm(forms.ModelForm):
    class Meta:
        model = SustanceCharacteristics
        exclude = ['obj', 'valid_molecular_formula']