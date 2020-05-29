
from django import forms

from laboratory.models import Object, SustanceCharacteristics, Laboratory, ObjectFeatures


class SustanceObjectForm(forms.ModelForm):
    features = forms.CharField()
    laboratory = forms.CharField()
    class Meta:
        model = Object
        fields = [
            'name', 'synonym',
            'code', 'is_public',
            'description',
            'model', 'serie', 'plaque'
        ]
        exclude = ['laboratory', 'features']

class SustanceCharacteristicsForm(forms.ModelForm):
    white_organ = forms.CharField()
    h_code = forms.CharField()
    class Meta:
        model = SustanceCharacteristics
        exclude = ['obj', 'white_organ', 'h_code']