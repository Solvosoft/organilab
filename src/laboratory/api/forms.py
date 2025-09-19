from django import forms
from django.conf import settings

from laboratory.models import Laboratory, OrganizationStructure, Shelf


class CommentInformForm(forms.Form):
    inform = forms.IntegerField(required=True)


class OrganizationLaboratoryForm(forms.Form):
    laboratory = forms.ModelChoiceField(
        queryset=Laboratory.objects.using(settings.READONLY_DATABASE)
    )
    organization = forms.ModelChoiceField(
        queryset=OrganizationStructure.objects.using(settings.READONLY_DATABASE)
    )


class ShelfObjectLabviewForm(OrganizationLaboratoryForm):
    shelf = forms.ModelChoiceField(
        queryset=Shelf.objects.using(settings.READONLY_DATABASE)
    )
