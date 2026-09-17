from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.files import FileChunkedUpload
from djgentelella.widgets.selects import AutocompleteSelect, AutocompleteSelectMultiple

from ambiental.ambiental_defaults import EXTRA_FIELDS, KEY_NORMALIZER, KEY_RESOURCE_TYPE
from ambiental.models import ConsumptionRecord, MeasurementPoint, NormalizationBase
from laboratory.models import Catalog, Provider
from report.forms import ReportBase
from risk_management.models import Buildings


class MeasurementPointForm(GTForm, forms.ModelForm):
    class Meta:
        model = MeasurementPoint
        fields = [
            "code",
            "name",
            "point_type",
            "resource_type",
            "building",
            "laboratories",
            "meters_count",
        ]
        widgets = {
            "code": genwidgets.TextInput,
            "name": genwidgets.TextInput,
            "point_type": genwidgets.Select,
            "resource_type": genwidgets.Select,
            "building": AutocompleteSelect(
                "ambiental_buildings", attrs={"data-s2filter-org_pk": "#org"}
            ),
            "laboratories": AutocompleteSelectMultiple(
                "ambiental_laboratories", attrs={"data-s2filter-org_pk": "#org"}
            ),
            "meters_count": genwidgets.NumberInput,
        }


class BuildingFilterForm(GTForm, forms.Form):
    """El selector de edificio de la cabecera: el camino corto del registro."""

    building = forms.ModelChoiceField(
        queryset=Buildings.objects.none(),
        required=False,
        label=_("Building"),
        widget=AutocompleteSelect(
            "ambiental_buildings", attrs={"data-s2filter-org_pk": "#org"}
        ),
    )


class ConsumptionRecordForm(GTForm, forms.ModelForm):
    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Los proveedores son por laboratorio: sin acotarlos, el select listaría
        # los gestores de todas las instituciones.
        providers = Provider.objects.none()
        if organization is not None:
            providers = Provider.objects.filter(
                Q(laboratory__in=organization.get_my_laboratories) | Q(laboratory__isnull=True)
            )
        self.fields["waste_manager"].queryset = providers
        for name, label in EXTRA_FIELDS.items():
            self.fields[name] = forms.CharField(
                label=label,
                required=False,
                widget=genwidgets.TextInput(attrs={"data-ambiental-extra": name}),
            )
        self.fields["unit"].required = False

    class Meta:
        model = ConsumptionRecord
        fields = [
            "point",
            "period_start",
            "period_end",
            "quantity",
            "unit",
            "unit_cost",
            "total_cost",
            "document",
            "treatment",
            "waste_manager",
            "note",
        ]
        widgets = {
            "point": AutocompleteSelect(
                "ambiental_points",
                attrs={
                    "data-s2filter-org_pk": "#org",
                    "data-s2filter-building": "#id_building",
                    "data-ambiental-point": "1",
                },
            ),
            "period_start": genwidgets.DateInput,
            "period_end": genwidgets.DateInput,
            "quantity": genwidgets.NumberInput(attrs={"step": "any", "min": "0"}),
            "unit": genwidgets.Select,
            "unit_cost": genwidgets.NumberInput(attrs={"step": "any", "min": "0"}),
            "total_cost": genwidgets.NumberInput(attrs={"step": "any", "min": "0"}),
            "document": FileChunkedUpload,
            "treatment": genwidgets.Select(attrs={"data-ambiental-waste": "1"}),
            "waste_manager": genwidgets.Select(attrs={"data-ambiental-waste": "1"}),
            "note": genwidgets.Textarea(attrs={"rows": 2}),
        }


class NormalizationBaseForm(GTForm, forms.ModelForm):
    class Meta:
        model = NormalizationBase
        fields = ["building", "normalizer", "year", "value"]
        widgets = {
            "building": AutocompleteSelect(
                "ambiental_buildings", attrs={"data-s2filter-org_pk": "#org"}
            ),
            "normalizer": genwidgets.Select,
            "year": genwidgets.NumberInput(attrs={"min": "1900", "max": "2200"}),
            "value": genwidgets.NumberInput(attrs={"step": "any", "min": "0"}),
        }


class AmbientalReportForm(ReportBase):
    """Filtros comunes de los reportes ambientales.

    ``cleaned_data`` termina guardado como JSON en ``TaskReport.data``: los campos de
    modelo se limpian a listas de pks.
    """

    building = forms.ModelMultipleChoiceField(
        queryset=Buildings.objects.none(),
        required=False,
        label=_("Buildings"),
        widget=genwidgets.SelectMultiple,
    )
    resource_type = forms.ModelMultipleChoiceField(
        queryset=Catalog.objects.filter(key=KEY_RESOURCE_TYPE),
        required=False,
        label=_("Resource type"),
        widget=genwidgets.SelectMultiple,
    )
    period = forms.CharField(
        widget=genwidgets.DateRangeInput, required=False, label=_("Period")
    )

    def __init__(self, *args, org_pk=None, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if org_pk:
            self.fields["building"].queryset = Buildings.objects.filter(organization__pk=org_pk)

    def clean_building(self):
        return list(self.cleaned_data["building"].values_list("pk", flat=True))

    def clean_resource_type(self):
        return list(self.cleaned_data["resource_type"].values_list("pk", flat=True))


class IndicatorReportForm(AmbientalReportForm):
    normalizer = forms.ModelMultipleChoiceField(
        queryset=Catalog.objects.filter(key=KEY_NORMALIZER),
        required=False,
        label=_("Normalizer"),
        widget=genwidgets.SelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["period"].required = True

    def clean_normalizer(self):
        return list(self.cleaned_data["normalizer"].values_list("pk", flat=True))


class ComparisonReportForm(AmbientalReportForm):
    comparison_period = forms.CharField(
        widget=genwidgets.DateRangeInput, required=True, label=_("Period to compare with")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["period"].required = True
