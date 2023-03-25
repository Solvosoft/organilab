from django import forms

class ValidateReviewSubstanceForm(forms.Form):
    org_pk = forms.IntegerField(required=True)
    showapprove = forms.BooleanField(required=True)