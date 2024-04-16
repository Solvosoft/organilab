from django import forms
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from djgentelella.forms.forms import GTForm
from djgentelella.widgets.wysiwyg import TextareaWysiwyg

from laboratory.models import OrganizationStructureRelations
from laboratory.utils import get_user_laboratories
from risk_management.models import RiskZone, IncidentReport, ZoneType
from djgentelella.widgets import core as djgentelella
from urllib.parse import quote
from django.urls import reverse


class RiskZoneCreateForm(forms.ModelForm,GTForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        org_pk = kwargs.pop('org_pk', None)
        super().__init__(*args, **kwargs)
        queryset = get_user_laboratories(user)

        if queryset.exists() and org_pk:
            extra_labs = OrganizationStructureRelations.objects.filter(organization__pk=org_pk,
                                                                 content_type=ContentType.objects.filter(
                                                                     app_label='laboratory',
                                                                     model='laboratory'
                                                                 ).first(),
                                                                 ).values_list("object_id", flat=True)

            queryset = queryset.filter(Q(organization__pk=org_pk) | Q(pk__in=extra_labs)).distinct()

        self.fields['laboratories'].queryset = queryset
        self.fields['zone_type'].widget.attrs['add_url'] = reverse(
            'riskmanagement:zone_type_add', args=(org_pk,))+ '?tipo=' +quote('zone_type')
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
            'zone_type': djgentelella.SelectWithAdd(attrs={'add_url': "#", 'data-otrono': 1}),
        }
class IncidentReportForm(GTForm,forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        org_pk = kwargs.pop('org_pk', None)
        super().__init__(*args, **kwargs)
        queryset = get_user_laboratories(user)
        if org_pk:
            queryset = queryset.filter(organization__pk=org_pk)
        self.fields['laboratories'].queryset = queryset

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

class ZoneTypeForm(GTForm, forms.ModelForm):
    class Meta:
        model = ZoneType
        fields = '__all__'
        widgets = {
            'name': djgentelella.TextInput(),
            'priority_validator': djgentelella.SelectMultiple()
        }
