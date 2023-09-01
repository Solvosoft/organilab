from django import forms
from django.conf import settings
from django.core.validators import RegexValidator
from djgentelella.widgets.wysiwyg import TextareaWysiwyg

from .models import ProcedureStep, Procedure, MyProcedure, CommentProcedureStep
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from laboratory.models import Object,Catalog,Shelf
from django.utils.translation import gettext_lazy as _


class MyProcedureForm(forms.ModelForm, GTForm):
    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)
        super(MyProcedureForm, self).__init__(*args, **kwargs)

        if org_pk:
            self.fields['custom_procedure'].queryset = Procedure.objects.filter()
        else:
            self.fields['custom_procedure'].queryset = Procedure.objects.none()

    class Meta:
        model = MyProcedure
        fields = ['name', 'custom_procedure']
        widgets = {'name': genwidgets.TextInput(attrs={'required': True}),
                   'custom_procedure': genwidgets.Select(attrs={'required':True}),
                   }


class CommentProcedureStepForm(forms.ModelForm, GTForm):
    class Meta:
        model = CommentProcedureStep
        fields = ['created_by', 'comment']
        widgets = {'created_by': genwidgets.HiddenInput,
                   'comment': genwidgets.Textarea,
                   }


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
    procedure_description = forms.CharField(widget=genwidgets.Textarea(), label= _("Description"), required=True)


class ObjectForm(GTForm, forms.Form):
    object = forms.ModelChoiceField(widget=genwidgets.Select(attrs={'data-dropdownparent': '#object_modal'}), queryset=Object.objects.all(), label= _('Object'), required=True)
    quantity = forms.CharField(widget=genwidgets.TextInput(), max_length=20, label= _('Amount'), required=True)
    unit = forms.ModelChoiceField(widget=genwidgets.Select(attrs={'data-dropdownparent': '#object_modal'}), queryset=Catalog.objects.filter(key='units'), label=_('Unit'), required=True)


class StepForm(GTForm, forms.Form):
    title = forms.CharField(widget=genwidgets.TextInput, label=_('Title'))
    description = forms.CharField(widget=TextareaWysiwyg,
                                  label=_('Description'))


class ReservationForm(GTForm, forms.Form):
    initial_date = forms.DateTimeField(widget=genwidgets.DateTimeInput, input_formats=settings.DATETIME_INPUT_FORMATS, required=True, label=_("Initial Date"))
    final_date = forms.DateTimeField(widget=genwidgets.DateTimeInput, input_formats=settings.DATETIME_INPUT_FORMATS, required=True, label=_("Final Date"))

    def clean(self):
        cleaned_data = super().clean()
        initial_date = cleaned_data.get('initial_date')
        final_date = cleaned_data.get('final_date')
        if initial_date and final_date:
          difference= (final_date-initial_date).days
          if difference<0:
              self.add_error('final_date', _("Final date can't be lower than initial date"))


class ValidateProcedureReservationForm(ReservationForm):
    procedure= forms.ModelChoiceField(widget=genwidgets.Select(), queryset=Procedure.objects.all(), required=True)


class AddObjectStepForm(GTForm, forms.Form):
    unit = forms.ModelChoiceField(queryset=Catalog.objects.filter(key="units"), required=True)
    object = forms.ModelChoiceField(queryset=Object.objects.all(), required=True)
    quantity = forms.FloatField(widget=genwidgets.TextInput, required=True, min_value=settings.DEFAULT_MIN_QUANTITY)

