from django import forms
from djgentelella.widgets.wysiwyg import TextareaWysiwyg

from .models import ProcedureStep, Procedure
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from laboratory.models import Object,Catalog,Shelf
from django.utils.translation import gettext_lazy as _
from organilab.settings import DATETIME_INPUT_FORMATS


class ProcedureForm(forms.ModelForm, GTForm):
    class Meta:
        model = Procedure
        fields = ['title', 'description']
        widgets = {
            'description': TextareaWysiwyg,
            'title':genwidgets.TextInput()
        }


class ProcedureStepForm(forms.ModelForm,GTForm):
    class Meta:
        model = ProcedureStep
        fields = ['title', 'description']
        widgets = {
            'description': TextareaWysiwyg,
            'title': genwidgets.TextInput
        }


class ObservationForm(forms.Form):
    description = forms.CharField(widget=genwidgets.Textarea(), label= _("Description"))


class ObjectForm(GTForm, forms.Form):
    object = forms.ModelChoiceField(widget=genwidgets.Select(attrs={'data-dropdownparent': '#object_modal'}), queryset=Object.objects.all(), label= _('Object'), required=True)
    quantity = forms.CharField(widget=genwidgets.TextInput(), max_length=20, label= _('Amount'), required=True)
    unit = forms.ModelChoiceField(widget=genwidgets.Select(attrs={'data-dropdownparent': '#object_modal'}), queryset=Catalog.objects.filter(key='units'), label=_('Unit'), required=True)


class StepForm(GTForm, forms.Form):
    title = forms.CharField(widget=genwidgets.TextInput, label=_('Title'))
    description = forms.CharField(widget=TextareaWysiwyg,
                                  label=_('Description'))


class ReservationForm(GTForm, forms.Form):
    initial_date = forms.DateTimeField(widget=genwidgets.DateTimeInput, input_formats=DATETIME_INPUT_FORMATS, required=False, label=_("Initial Date"))
    final_date = forms.DateTimeField(widget=genwidgets.DateTimeInput, input_formats=DATETIME_INPUT_FORMATS, required=False, label=_("Final Date"))
