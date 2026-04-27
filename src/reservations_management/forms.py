from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from .models import Reservations, ReservedProducts


class ReservationActionForm(GTForm, ModelForm):
    class Meta:
        model = Reservations
        fields = ['comments']
        widgets = {
            'comments': genwidgets.Textarea(),
        }


class ReturnProductForm(GTForm, forms.Form):
    amount_returned = forms.FloatField(
        required=False,
        min_value=0,
        widget=genwidgets.NumberInput(),
        label=_("Amount to return"),
    )
    reserved_boxes = forms.MultipleChoiceField(
        choices=[],
        widget=genwidgets.SelectMultiple,
        required=False,
        label=_("Boxes to return"),
    )

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        if product:
            if product.shelf_object.is_box:
                self.fields['reserved_boxes'].choices = [
                    (b['code'], f"{b['code']} ({b['units']} units)")
                    for b in product.reserved_boxes
                ]
                del self.fields['amount_returned']
            else:
                del self.fields['reserved_boxes']

    def clean(self):
        cleaned_data = super().clean()
        if not self.product:
            return cleaned_data
        if self.product.shelf_object.is_box:
            if not cleaned_data.get('reserved_boxes'):
                raise forms.ValidationError(_("Select at least one box to return."))
        else:
            amount = cleaned_data.get('amount_returned')
            if not amount or amount <= 0:
                raise forms.ValidationError(_("Amount to return must be greater than 0."))
            if amount > self.product.amount_required:
                raise forms.ValidationError(
                    _("Amount to return cannot exceed the required amount (%(max)s).") % {
                        'max': self.product.amount_required
                    }
                )
        return cleaned_data
