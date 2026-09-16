from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.files import FileChunkedUpload
from djgentelella.widgets.selects import AutocompleteSelect, AutocompleteSelectMultiple

from ambiental.ambiental_defaults import EXTRA_FIELDS
from ambiental.models import ConsumptionRecord, MeasurementPoint
from laboratory.models import Provider
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
