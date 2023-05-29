from django import forms

class ValidateReviewSubstanceForm(forms.Form):
    org_pk = forms.IntegerField(required=True)
    showapprove = forms.BooleanField(required=False)


class CommentProcedureStepForm(forms.Form):
    procedure_step = forms.IntegerField(required=True)