from django import forms

from laboratory.utils import get_user_laboratories
from risk_management.models import RiskZone


class RiskZoneCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['laboratories'].queryset = get_user_laboratories(user)

    def save(self, commit=True):
        priority = self.instance.zone_type.get_priority(self.instance.num_workers)
        self.instance.priority = priority
        return super().save(commit=commit)

    class Meta:
        model = RiskZone
        exclude = ['priority']