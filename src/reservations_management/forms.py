from django.forms import ModelForm
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from .models import Reservations


class ReservationsForm(GTForm, ModelForm):
    class Meta:
        model=Reservations
        fields='__all__'
        widgets={
            'user': genwidgets.Select(),
            'status': genwidgets.Select(),
            'laboratory': genwidgets.Select(),
            'comments': genwidgets.Textarea(),
            'is_massive': genwidgets.CheckboxInput()
        }
