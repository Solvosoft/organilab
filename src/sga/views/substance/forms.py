from django import forms
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.selects import (
    AutocompleteSelect,
    AutocompleteSelectMultiple,
)
from djgentelella.widgets.tagging import TaggingInput

from laboratory.models import Laboratory, OrganizationStructure
from sga.gtselects import (
    get_user_laboratories_queryset,
    get_user_organizations_queryset,
)
from sga.models import (
    Substance,
    SubstanceCharacteristics,
    DangerIndication,
    WarningWord,
    PrudenceAdvice,
    SecurityLeaf,
    ReviewSubstance,
    RecipientSize,
)
from sga.models import SubstanceObservation


class SustanceObjectForm(GTForm, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SustanceObjectForm, self).__init__(*args, **kwargs)
        self.fields["comercial_name"].label = _("Substance name")

    class Meta:
        model = Substance
        fields = [
            "comercial_name",
            "synonymous",
            "features",
            "description",
            "brand",
            "organization",
        ]
        widgets = {
            "comercial_name": genwidgets.TextInput,
            "synonymous": TaggingInput,
            "description": genwidgets.Textarea,
            "brand": genwidgets.TextInput,
            "organization": genwidgets.HiddenInput,
            "features": genwidgets.SelectMultiple,
        }


class SustanceCharacteristicsForm(GTForm, forms.ModelForm):
    class Meta:
        model = SubstanceCharacteristics
        exclude = [
            "substance",
            "valid_molecular_formula",
            "number_index",
            "number_ce",
            "object_related",
        ]
        widgets = {
            "iarc": genwidgets.Select,
            "imdg": genwidgets.Select,
            "white_organ": genwidgets.SelectMultiple,
            "bioaccumulable": genwidgets.YesNoInput,
            "molecular_formula": genwidgets.TextInput,
            "cas_id_number": genwidgets.TextInput,
            "is_precursor": genwidgets.YesNoInput,
            "precursor_type": genwidgets.Select,
            "h_code": genwidgets.SelectMultiple,
            "ue_code": genwidgets.SelectMultiple,
            "nfpa": genwidgets.SelectMultiple,
            "storage_class": genwidgets.SelectMultiple,
            "seveso_list": genwidgets.YesNoInput,
            "molecular_weight": genwidgets.TextInput,
            "concentration": genwidgets.TextInput,
            # genwidgets.FileInput sube por trozos a `upload_file_view` y deja en
            # el POST un token JSON que el widget resuelve contra ChunkedUpload;
            # por eso no mira request.FILES.
            "security_sheet": genwidgets.FileInput,
            "img_representation": genwidgets.FileInput,
            "density": genwidgets.TextInput,
            "is_dangerous": genwidgets.YesNoInput,
            "has_threshold": genwidgets.YesNoInput(
                shparent=".form-group",
                attrs={"rel": ["#id_threshold"]},
            ),
            "threshold": genwidgets.TextInput,
            "is_pure": genwidgets.YesNoInput,
        }


class DangerIndicationForm(GTForm, forms.ModelForm):

    def __init__(self, *arg, **kwargs):
        super(DangerIndicationForm, self).__init__(*arg, **kwargs)
        self.fields["warning_words"].required = False

    class Meta:
        model = DangerIndication
        fields = "__all__"
        widgets = {
            "code": genwidgets.TextInput,
            "description": genwidgets.Textarea,
            "warning_words": genwidgets.Select(),
            "warning_class": genwidgets.SelectMultiple(),
            "warning_category": genwidgets.SelectMultiple(),
            "prudence_advice": genwidgets.SelectMultiple(),
            "danger_type": genwidgets.TextInput,
        }


class WarningWordForm(GTForm, forms.ModelForm):
    class Meta:
        model = WarningWord
        fields = "__all__"
        widgets = {
            "name": genwidgets.TextInput,
            "weigth": genwidgets.NumberInput,
        }


class PrudenceAdviceForm(GTForm, forms.ModelForm):
    class Meta:
        model = PrudenceAdvice
        fields = "__all__"
        widgets = {
            "code": genwidgets.TextInput,
            "name": genwidgets.TextInput,
            "prudence_advice_help": genwidgets.Textarea,
        }


class ObservationForm(GTForm, forms.ModelForm):
    class Meta:
        model = SubstanceObservation
        fields = ["description"]

        widgets = {"description": genwidgets.Textarea}


class SecurityLeafForm(GTForm, forms.ModelForm):

    def __init__(self, *arg, **kwargs):
        super(SecurityLeafForm, self).__init__(*arg, **kwargs)
        fields = self.fields
        for field in fields.keys():
            if field not in ["provider", "substance"]:
                self.fields[str(field)].widget = genwidgets.Textarea()
            if field in ["register_number", "reach_number", "reference"]:
                self.fields[str(field)].widget = genwidgets.TextInput()

        self.fields["provider"].required = False
        self.fields["other_info"].label = _("Other Information")

    class Meta:
        model = SecurityLeaf
        exclude = ["substance"]
        fields = "__all__"
        widgets = {"provider": genwidgets.Select}


class ReviewSubstanceForm(GTForm, forms.ModelForm):
    class Meta:
        model = ReviewSubstance
        fields = "__all__"
        widgets = {
            "substance": genwidgets.HiddenInput,
            "note": genwidgets.NumberInput,
            "is_approved": genwidgets.HiddenInput,
            "organization": genwidgets.HiddenInput,
            "created_by": genwidgets.HiddenInput,
        }


class RecipientSizeForm(GTForm, forms.ModelForm):
    class Meta:
        model = RecipientSize
        fields = "__all__"
        widgets = {
            "name": genwidgets.TextInput,
            "heigth": genwidgets.NumberInput,
            "heigth_unit": genwidgets.Select,
            "width": genwidgets.NumberInput,
            "width_unit": genwidgets.Select,
        }


class SendToReviewForm(GTForm, forms.ModelForm):
    organization = forms.ModelChoiceField(
        queryset=OrganizationStructure.objects.none(),
        label=_("Organization"),
        widget=AutocompleteSelect(
            "user_organization_loop",
            attrs={
                "data-related": "true",
                "data-pos": 0,
                "data-groupname": "send_to_review",
                "data-s2filter-organization": "#id_organization",
                "data-s2filter-org_pk": "#id_organization",
            },
        ),
    )
    # Una sustancia se solicita a la vez para todos los laboratorios que la
    # necesitan, así que se eligen varios en un solo envío.
    laboratories = forms.ModelMultipleChoiceField(
        queryset=Laboratory.objects.none(),
        label=_("Laboratories"),
        widget=AutocompleteSelectMultiple(
            "user_laboratory_loop",
            attrs={
                "data-related": "true",
                "data-pos": 1,
                "data-groupname": "send_to_review",
                "data-s2filter-organization": "#id_organization",
                "data-s2filter-org_pk": "#id_organization",
            },
        ),
    )

    def __init__(self, *args, user=None, org_pk=None, **kwargs):
        super(SendToReviewForm, self).__init__(*args, **kwargs)
        self.fields["laboratories"].required = True
        self.fields["organization"].required = True
        # Los lookups solo restringen lo que muestra el desplegable; sin acotar
        # también el queryset, la validación aceptaría cualquier pk y permitiría
        # enviar una sustancia a una organización o laboratorio ajenos.
        self.fields["organization"].queryset = get_user_organizations_queryset(user)
        self.fields["laboratories"].queryset = get_user_laboratories_queryset(
            user, org_pk
        )

    class Meta:
        model = Substance
        fields = ["organization", "laboratories"]
