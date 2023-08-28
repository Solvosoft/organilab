from django import forms
from django.conf import settings
from laboratory.models import Shelf


class ShelfFilterForm(forms.Form):
    shelf = forms.ModelChoiceField(queryset=Shelf.objects.none())

    def __init__(self, laboratory, *args, **kwargs):
        self.laboratory = laboratory
        super().__init__(*args, **kwargs)
        self.fields['shelf'].queryset = Shelf.objects.using(settings.READONLY_DATABASE).filter(
            furniture__labroom__laboratory=self.laboratory
        )
