from ckeditor.widgets import CKEditorWidget
from django import forms
from django.conf import settings
from laboratory.utils import get_user_laboratories
from risk_management.models import RiskZone, IncidentReport


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
            'causes': CKEditorWidget(attrs={'lang': settings.LANGUAGE_CODE }),
            'infraestructure_impact': CKEditorWidget(attrs={'lang': settings.LANGUAGE_CODE }),
            'people_impact': CKEditorWidget(attrs={'lang': settings.LANGUAGE_CODE }),
            'environment_impact': CKEditorWidget(attrs={'lang': settings.LANGUAGE_CODE }),
            'result_of_plans': CKEditorWidget(attrs={'lang': settings.LANGUAGE_CODE }),
            'mitigation_actions': CKEditorWidget(attrs={'lang': settings.LANGUAGE_CODE }),
            'recomendations': CKEditorWidget(attrs={'lang': settings.LANGUAGE_CODE }),
        }