from django import forms


class CommentProcedureStepForm(forms.Form):
    procedure_step = forms.IntegerField(required=True)
