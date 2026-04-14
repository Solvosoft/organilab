from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from .models import Reservations, ReservedProducts


class ReservationsForm(GTForm, ModelForm):
    class Meta:
        model = Reservations
        fields = ["status", "comments"]
        widgets = {
            "status": genwidgets.Select(),
            "comments": genwidgets.Textarea(),
        }


class ProductForm(ModelForm, GTForm):

    reserved_boxes = forms.MultipleChoiceField(
        choices=[],
        widget=genwidgets.SelectMultiple,
        required=False,
        label=_("Boxes to return"),
    )

    class Meta:
        model = ReservedProducts
        fields = [
            "is_returnable",
            "status",
            "amount_required",
            "amount_returned",
            "initial_date",
            "final_date",
            "reserved_boxes",
        ]
        widgets = {
            "amount_required": genwidgets.NumberInput(attrs={"readonly": "True"}),
            "amount_returned": genwidgets.NumberInput(),
            "is_returnable": genwidgets.CheckboxInput(),
            "status": genwidgets.Select(
                attrs={"data-dropdownparent": "#exampleModal", "id": "reserveStatus"}
            ),
            "initial_date": genwidgets.TextInput(attrs={"readonly": "True"}),
            "final_date": genwidgets.TextInput(attrs={"readonly": "True"}),
        }
