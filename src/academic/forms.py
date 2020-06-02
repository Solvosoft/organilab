from ckeditor.widgets import CKEditorWidget
from django import forms
from .models import ProcedureStep, Procedure
from django.conf import settings


class ProcedureForm(forms.ModelForm):
    class Meta:
        model = Procedure
        fields = ['title', 'description']
        widgets = {
            'description': CKEditorWidget(attrs={'lang': settings.LANGUAGE_CODE }),
        }

class ProcedureStepForm(forms.ModelForm):
    class Meta:
        model = ProcedureStep
        fields = ['title', 'description']
        widgets = {
            'description': CKEditorWidget(attrs={'lang': settings.LANGUAGE_CODE }),
        }