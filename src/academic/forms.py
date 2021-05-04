from ckeditor.widgets import CKEditorWidget
from django import forms
from .models import ProcedureStep, Procedure
from django.conf import settings
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from laboratory.models import Object,Catalog,Shelf
from django.utils.translation import ugettext_lazy as _
from organilab.settings import DATETIME_INPUT_FORMATS

class ProcedureForm(forms.ModelForm):
    class Meta:
        model = Procedure
        fields = ['title', 'description']
        widgets = {
            'description': CKEditorWidget(attrs={'lang': settings.LANGUAGE_CODE }),
            'title':genwidgets.TextInput()
        }

class ProcedureStepForm(forms.ModelForm,GTForm):
    class Meta:
        model = ProcedureStep
        fields = ['title', 'description']
        widgets = {
            'description': CKEditorWidget(attrs={'lang': settings.LANGUAGE_CODE }),
            'title': genwidgets.TextInput
        }

class ObservationForm(GTForm, forms.Form):
    description = forms.CharField(widget=genwidgets.Textarea(), label= _("Description"))


class ObjectForm(GTForm, forms.Form):
    object = forms.ModelChoiceField(widget=genwidgets.Select(), queryset=Object.objects.all(), label= _('Object'), required=True)
    quantity = forms.CharField(widget=genwidgets.TextInput(), max_length=20, label= _('Amount'), required=True)
    unit = forms.ModelChoiceField(widget=genwidgets.Select(), queryset=Catalog.objects.filter(key='units'), label=_('Unit'), required=True)

class StepForm(GTForm, forms.Form):
    title = forms.CharField(widget=genwidgets.TextInput, label=_('title'))
    description = forms.CharField(widget=CKEditorWidget(attrs={'lang': settings.LANGUAGE_CODE }),
                                  label=_('Description'))
class ReservationForm(GTForm, forms.Form):
    shelf = forms.ModelChoiceField(widget=genwidgets.Select, queryset=Shelf.objects.all(), label=_("Shelf"),
                                   required=True)
    initial_date = forms.DateTimeField(widget=genwidgets.DateInput, input_formats=DATETIME_INPUT_FORMATS, required=False)
    final_date = forms.DateTimeField(widget=genwidgets.DateInput, input_formats=DATETIME_INPUT_FORMATS, required=False)

    def __init__(self, *args, **kwargs):
        super(ReservationForm, self).__init__(*args, **kwargs)
        shelf = Shelf.objects.filter(furniture__labroom__laboratory__id=int(60))
        self.fields['shelf'].queryset = shelf
