from django import forms
from djgentelella.widgets.wysiwyg import TextareaWysiwyg

from laboratory.utils import get_user_laboratories
from risk_management.models import RiskZone, IncidentReport
from djgentelella.widgets import core as djgentelella


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

class IncidentReportForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['laboratories'].queryset = get_user_laboratories(user)

    class Meta:
        model = IncidentReport
        fields = '__all__'
        widgets = {
            'causes': TextareaWysiwyg,
            "incident_date": djgentelella.DateInput,
            'infraestructure_impact': TextareaWysiwyg,
            'people_impact': TextareaWysiwyg,
            'environment_impact': TextareaWysiwyg,
            'result_of_plans': TextareaWysiwyg,
            'mitigation_actions': TextareaWysiwyg,
            'recomendations': TextareaWysiwyg,
        }