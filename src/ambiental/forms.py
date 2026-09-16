from django import forms
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.selects import AutocompleteSelect, AutocompleteSelectMultiple

from ambiental.models import MeasurementPoint


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
