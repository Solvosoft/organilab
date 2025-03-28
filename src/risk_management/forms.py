from django import forms
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from djgentelella.forms.forms import GTForm
from djgentelella.widgets.wysiwyg import TextareaWysiwyg

from .models import Regent
from laboratory.models import OrganizationStructureRelations, Laboratory
from laboratory.utils import get_user_laboratories, get_users_from_organization
from risk_management.models import RiskZone, IncidentReport, ZoneType, Buildings
from djgentelella.widgets import core as djgentelella
from djgentelella.widgets import core as genwidgets
from urllib.parse import quote
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .utils import get_regents_from_organization


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

class BuildingsForm(GTForm, forms.ModelForm):
    default_render_type = "as_grid"
    grid_representation = [
        [
            ["name",
             "is_asociaty_buildings",
             "nearby_buildings",
             "laboratories",
             "has_water_resources",
             "has_nearby_sites",
             "security_plan",
             "plans"
             ],
            [
            "phone",
            "regents",
             "manager",
             "area",
             "regulatory_plans",
             "geolocation"
             ]

        ],


    ]
    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)
        instance = kwargs.get('instance', None)
        super(BuildingsForm, self).__init__(*args, **kwargs)
        self.fields['geolocation'].widget.attrs['class'] = 'form-control'
        self.fields['geolocation'].label = _('Geolocation')


        if org_pk:
            self.fields['regents'].queryset = (
                Regent.objects.filter(organization__pk=org_pk))
            self.fields['laboratories'].queryset = (
                Laboratory.objects.filter(organization__pk=org_pk))
            if instance:
                self.fields['nearby_buildings'].queryset = (
                    Buildings.objects.filter(organization__pk=org_pk).
                    exclude(pk=instance.pk))
            else:
                self.fields['nearby_buildings'].queryset = (
                Buildings.objects.filter(organization__pk=org_pk))
            self.fields['manager'].queryset = (
                User.objects.filter(pk__in=get_users_from_organization(org_pk)))

    class Meta:
        model = Buildings
        fields = ['name', 'laboratories', 'is_asociaty_buildings',
                  'nearby_buildings',  'geolocation', 'phone', 'manager',
                  'area', 'plans', 'security_plan', 'has_water_resources',
                  'has_nearby_sites', 'regents', 'regulatory_plans']
        widgets = {
            'name': djgentelella.TextInput,
            'laboratories': genwidgets.SelectMultiple(),
            'is_asociaty_buildings': djgentelella.YesNoInput(
                shparent='.asgrid',
                attrs={
                    "rel": ["#id_nearby_buildings"]
                },
            ),
            'nearby_buildings': genwidgets.SelectMultiple(),
            'geolocation': djgentelella.TextInput,
            'phone': djgentelella.TextInput,
            'manager': djgentelella.Select,
            'regents': genwidgets.SelectMultiple(),
            'has_water_resources': djgentelella.YesNoInput,
            'has_nearby_sites': djgentelella.FileInput,
            'area': djgentelella.FloatInput,
            'plans': djgentelella.FileInput,
            'security_plan': djgentelella.FileInput,
            'regulatory_plans': djgentelella.FileInput,

        }


class RegentForm(GTForm, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)
        super(RegentForm, self).__init__(*args, **kwargs)
        self.fields['user'].queryset = (User.objects.filter(
            pk__in=get_users_from_organization(org_pk)).
                                        exclude(
            pk__in=get_regents_from_organization(org_pk)).order_by('username'))

    class Meta:
        model = Regent
        fields = ["user"]
        widgets = {
            'user': djgentelella.Select
        }
