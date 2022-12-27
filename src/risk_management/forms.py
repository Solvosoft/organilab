from django import forms
from djgentelella.forms.forms import GTForm
from djgentelella.widgets.wysiwyg import TextareaWysiwyg
from laboratory.utils import get_user_laboratories
from risk_management.models import RiskZone, IncidentReport
from djgentelella.widgets import core as djgentelella


class RiskZoneCreateForm(forms.ModelForm,GTForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        org_pk = kwargs.pop('org_pk', None)
        super().__init__(*args, **kwargs)
        queryset = get_user_laboratories(user)

        if queryset.exists() and org_pk:
            queryset = queryset.filter(organization__pk=org_pk)

        self.fields['laboratories'].queryset = queryset

    def save(self, commit=True):
        priority = self.instance.zone_type.get_priority(self.instance.num_workers)
        self.instance.priority = priority
        return super().save(commit=commit)

    class Meta:
        model = RiskZone
        exclude = ['priority', 'organization','created_by']
        widgets = {
            'name': djgentelella.TextInput,
            "laboratories": djgentelella.SelectMultiple,
            'num_workers': djgentelella.NumberInput,
            'zone_type': djgentelella.Select,
        }
class IncidentReportForm(GTForm,forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['laboratories'].queryset = get_user_laboratories(user)

    class Meta:
        model = IncidentReport
        exclude = ('organization', 'created_by')
        widgets = {
            'short_description':djgentelella.TextInput,
            'causes': TextareaWysiwyg,
            "incident_date": djgentelella.DateInput,
            'infraestructure_impact': TextareaWysiwyg,
            'people_impact': TextareaWysiwyg,
            'laboratories': djgentelella.SelectMultiple(),
            'environment_impact': TextareaWysiwyg,
            'result_of_plans': TextareaWysiwyg,
            'mitigation_actions': TextareaWysiwyg,
            'recomendations': TextareaWysiwyg,
        }