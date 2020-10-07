from django.forms import ModelForm
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from .models import Reservations


class ReservationsForm(GTForm, ModelForm):

    class Meta:
        model = Reservations
        fields = ['status','comments']
        widgets = {
            'status': genwidgets.Select(),
            'comments': genwidgets.Textarea(),
        }
