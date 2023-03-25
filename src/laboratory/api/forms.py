from django import forms

class CommentInformForm(forms.Form):
    inform = forms.IntegerField(required=True)