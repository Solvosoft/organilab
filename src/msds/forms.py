from django import forms
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from djgentelella.widgets import core as genwidgets

from laboratory.models import Catalog
from sga.models import DangerIndication


class SDSUploadForm(forms.Form):
    file = forms.FileField(
        label=_("FDS File (PDF)"),
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )


class SDSConfirmForm(forms.Form):
    # --- Identification ---
    name = forms.CharField(
        label=_("Substance name"),
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    cas_id_number = forms.CharField(
        label=_("CAS number"),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    molecular_formula = forms.CharField(
        label=_("Molecular formula"),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    revision_date = forms.DateField(
        label=_("Revision date"),
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )

    # --- Physical properties ---
    density = forms.FloatField(
        label=_("Density"),
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
    )

    # --- Classifications ---
    iarc = forms.ModelChoiceField(
        label=_("IARC"),
        queryset=Catalog.objects.filter(key="IARC"),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    imdg = forms.ModelChoiceField(
        label=_("IMDG"),
        queryset=Catalog.objects.filter(key="IDMG"),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    h_code = forms.ModelMultipleChoiceField(
        label=_("H-codes"),
        queryset=DangerIndication.objects.all(),
        required=False,
        widget=genwidgets.SelectMultiple,
    )
    ue_code = forms.ModelMultipleChoiceField(
        label=_("EU codes"),
        queryset=Catalog.objects.filter(key="ue_code"),
        required=False,
        widget=genwidgets.SelectMultiple,
    )
    nfpa = forms.ModelMultipleChoiceField(
        label=_("NFPA"),
        queryset=Catalog.objects.filter(key="nfpa"),
        required=False,
        widget=genwidgets.SelectMultiple,
    )
    storage_class = forms.ModelMultipleChoiceField(
        label=_("Storage class"),
        queryset=Catalog.objects.filter(key="storage_class"),
        required=False,
        widget=genwidgets.SelectMultiple,
    )

    # --- Risks ---
    bioaccumulable = forms.NullBooleanField(
        label=_("Bioaccumulable"),
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select"},
            choices=[("", "---------"), (True, _("Yes")), (False, _("No"))],
        ),
    )
    is_precursor = forms.BooleanField(
        label=_("Is precursor"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    precursor_type = forms.ModelChoiceField(
        label=_("Precursor type"),
        queryset=Catalog.objects.filter(key="Precursor"),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    seveso_list = forms.BooleanField(
        label=_("Seveso list"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    white_organ = forms.ModelMultipleChoiceField(
        label=_("Target organs"),
        queryset=Catalog.objects.filter(key="white_organ"),
        required=False,
        widget=genwidgets.SelectMultiple,
    )
