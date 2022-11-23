from django import forms
from djgentelella.forms.forms import GTForm
from djgentelella.widgets.wysiwyg import TextareaWysiwyg
from laboratory.utils import get_user_laboratories
from risk_management.models import RiskZone, IncidentReport, ZoneType
from djgentelella.widgets import core as djgentelella


class RiskZoneCreateForm(forms.ModelForm, GTForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')

        super().__init__(*args, **kwargs)
        self.fields['laboratories'].queryset = get_user_laboratories(user)
        if 'instance' in kwargs:
            choices = self.fields['zone_type'].choices
            self.fields['zone_type'].widget = djgentelella.Select(choices=choices,
                                                                  attrs={'data-dropdownparent': '#update_zone_risk_modal'})


    def save(self, commit=True):
        priority = self.instance.zone_type.get_priority(self.instance.num_workers)
        self.instance.priority = priority
        return super().save(commit=commit)

    class Meta:
        model = RiskZone
        exclude = ['priority']
        fields = '__all__'
        widgets = {
            'name': djgentelella.TextInput,
            "laboratories": djgentelella.SelectMultiple,
            'num_workers': djgentelella.NumberInput,
            'zone_type': djgentelella.SelectWithAdd(attrs={'add_url': '/api/zonetypeview/formzonetype/',
                                                           #'data-otrono': 1,
                                                           'required': True}),

        }
class IncidentReportForm(GTForm,forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['laboratories'].queryset = get_user_laboratories(user)

    class Meta:
        model = IncidentReport
        fields = '__all__'
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


class ZoneTypeForm(forms.ModelForm):

    class Meta:
        model = ZoneType
        fields = '__all__'
        widgets = {
            'name': djgentelella.TextInput(attrs={'required': True}),
            'priority_validator': djgentelella.SelectMultiple(),
        }

