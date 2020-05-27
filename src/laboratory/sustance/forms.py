
from django import forms

from laboratory.models import Object, SustanceCharacteristics


class SustanceObjectForm(forms.ModelForm):

    class Meta:
        model = Object
        fields = [
            'name', 'synonym',
            'code', 'is_public',
            'description', 'features',
            'model', 'serie', 'plaque',
            'laboratory'
        ]

class SustanceCharacteristicsForm(forms.ModelForm):
    class Meta:
        model = SustanceCharacteristics
        exclude = ['obj']