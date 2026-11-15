from django import forms
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.files import FileChunkedUpload

from auth_and_perms.models import Profile
from laboratory.models import (
    ControlMeasurement,
    ControlMethod,
    ControlPoint,
    EquipmentActivityPlan,
    EquipmentDocument,
    OrganizationStructure,
    Provider,
    ShelfObjectFailure,
    ShelfObjectVerification,
)

HIDDEN = {
    "organization": genwidgets.HiddenInput,
    "created_by": genwidgets.HiddenInput,
    "shelfobject": genwidgets.HiddenInput,
}
PROFILE_FIELDS = ("responsible", "custodian", "acceptance_responsible", "authorized_users", "validator")


class EquipmentScopedFormMixin:
    """Acota los selects del formulario a la organización, el laboratorio y el equipo.

    Recibe ``org_pk``, ``lab_pk`` y ``shelfobject`` como kwargs. Los perfiles salen de
    los usuarios de la organización; los proveedores, de ``Provider.objects.for_laboratory``;
    el programa (``plan``), de los del mismo equipo.
    """

    def __init__(self, *args, org_pk=None, lab_pk=None, shelfobject=None, **kwargs):
        super().__init__(*args, **kwargs)
        organization = OrganizationStructure.objects.filter(pk=org_pk).first()
        profiles = (
            Profile.objects.filter(user__in=organization.users.all())
            if organization is not None else Profile.objects.none()
        )
        for name in PROFILE_FIELDS:
            if name in self.fields and hasattr(self.fields[name], "queryset"):
                self.fields[name].queryset = profiles
        for name in ("provider", "provider_of_maintenance"):
            if name in self.fields:
                self.fields[name].queryset = Provider.objects.for_laboratory(org_pk, lab_pk)
        if "plan" in self.fields:
            self.fields["plan"].queryset = EquipmentActivityPlan.objects.filter(shelfobject_id=shelfobject)


class ActivityPlanForm(EquipmentScopedFormMixin, GTForm, forms.ModelForm):
    class Meta:
        model = EquipmentActivityPlan
        fields = [
            "activity_kind", "name", "interval_value", "interval_unit", "start_date",
            "reminder_days_before", "responsible", "is_active", "notes",
        ]
        widgets = {
            "activity_kind": genwidgets.Select,
            "name": genwidgets.TextInput,
            "interval_value": genwidgets.NumberInput,
            "interval_unit": genwidgets.Select,
            "start_date": genwidgets.DateInput,
            "reminder_days_before": genwidgets.NumberInput,
            "responsible": genwidgets.Select,
            "is_active": genwidgets.YesNoInput,
            "notes": genwidgets.Textarea,
        }


class VerificationForm(EquipmentScopedFormMixin, GTForm, forms.ModelForm):
    class Meta:
        model = ShelfObjectVerification
        fields = [
            "plan", "verification_date", "verification_type", "result", "acceptance_criterion",
            "conformity", "responsible", "document", "observation",
        ]
        widgets = {
            "plan": genwidgets.Select,
            "verification_date": genwidgets.DateInput,
            "verification_type": genwidgets.TextInput,
            "result": genwidgets.Textarea,
            "acceptance_criterion": genwidgets.Textarea,
            "conformity": genwidgets.Select,
            "responsible": genwidgets.Select,
            "document": FileChunkedUpload,
            "observation": genwidgets.Textarea,
        }


class FailureForm(EquipmentScopedFormMixin, GTForm, forms.ModelForm):
    class Meta:
        model = ShelfObjectFailure
        fields = [
            "failure_date", "description", "blocked", "repair_done", "modifications", "provider",
            "responsible", "return_to_service_date", "verification_before_use", "impact_assessment",
            "report",
        ]
        widgets = {
            "failure_date": genwidgets.DateInput,
            "description": genwidgets.Textarea,
            "blocked": genwidgets.YesNoInput,
            "repair_done": genwidgets.Textarea,
            "modifications": genwidgets.Textarea,
            "provider": genwidgets.Select,
            "responsible": genwidgets.Select,
            "return_to_service_date": genwidgets.DateInput,
            "verification_before_use": genwidgets.Textarea,
            "impact_assessment": genwidgets.Textarea,
            "report": FileChunkedUpload,
        }


class EquipmentDocumentForm(EquipmentScopedFormMixin, GTForm, forms.ModelForm):
    class Meta:
        model = EquipmentDocument
        fields = ["document_type", "title", "version", "valid_from", "file"]
        widgets = {
            "document_type": genwidgets.Select,
            "title": genwidgets.TextInput,
            "version": genwidgets.TextInput,
            "valid_from": genwidgets.DateInput,
            "file": FileChunkedUpload,
        }


#: Widgets de los campos ISO que se suman a los formularios existentes.
CALIBRATION_ISO_WIDGETS = {
    "provider": genwidgets.Select,
    "certificate": FileChunkedUpload,
    "certificate_number": genwidgets.TextInput,
    "results": genwidgets.Textarea,
    "uncertainty": genwidgets.TextInput,
    "correction_factor": genwidgets.TextInput,
    "adjustments": genwidgets.Textarea,
    "acceptance_criterion": genwidgets.Textarea,
    "conformity": genwidgets.Select,
    "next_calibration_date": genwidgets.DateInput,
}
MAINTENANCE_ISO_WIDGETS = {
    "maintenance_type": genwidgets.Select,
    "plan": genwidgets.Select,
    "activities": genwidgets.SelectMultiple,
    "report": FileChunkedUpload,
    "affects_calibration": genwidgets.YesNoInput,
    "damage_details": genwidgets.Textarea,
}
EQUIPMENT_ISO_WIDGETS = {
    "internal_code": genwidgets.TextInput,
    "asset_number": genwidgets.TextInput,
    "brand": genwidgets.TextInput,
    "model": genwidgets.TextInput,
    "serial_number": genwidgets.TextInput,
    "photo": FileChunkedUpload,
    "software_name": genwidgets.TextInput,
    "software_version": genwidgets.TextInput,
    "firmware_version": genwidgets.TextInput,
    "magnitude": genwidgets.Select,
    "physical_location": genwidgets.TextInput,
    "equipment_status": genwidgets.Select,
    "use_restriction": genwidgets.Textarea,
    "measurement_unit": genwidgets.TextInput,
    "resolution": genwidgets.TextInput,
    "working_range": genwidgets.TextInput,
    "accuracy_tolerance": genwidgets.TextInput,
    "capacity": genwidgets.TextInput,
    "acceptance_criteria": genwidgets.Textarea,
    "metrological_requirements": genwidgets.Textarea,
    "acceptance_evidence": FileChunkedUpload,
    "acceptance_responsible": genwidgets.Select,
    "custodian": genwidgets.Select,
    "authorized_users": genwidgets.SelectMultiple,
    "access_restrictions": genwidgets.Textarea,
    "decommission_date": genwidgets.DateInput,
    "decommission_reason": genwidgets.Textarea,
    "final_disposition": genwidgets.Textarea,
}

#: Secciones de la ficha ISO para la plantilla: (título, campos).
EQUIPMENT_ISO_SECTIONS = (
    (_("Identification"), [
        "internal_code", "asset_number", "brand", "model", "serial_number", "magnitude",
        "software_name", "software_version", "firmware_version", "photo",
    ]),
    (_("Location and status"), ["physical_location", "equipment_status", "use_restriction"]),
    (_("Specifications"), [
        "measurement_unit", "resolution", "working_range", "accuracy_tolerance", "capacity",
        "acceptance_criteria", "metrological_requirements",
    ]),
    (_("Reception"), ["acceptance_evidence", "acceptance_responsible"]),
    (_("Responsibility"), ["custodian", "authorized_users", "access_restrictions"]),
    (_("Decommission"), ["decommission_date", "decommission_reason", "final_disposition"]),
)


# --- Cartas de control (F3) ----------------------------------------------------------

class ControlMethodForm(GTForm, forms.ModelForm):
    class Meta:
        model = ControlMethod
        fields = ["name", "description", "chart_type", "subgroup_size", "a2", "d3", "d4",
                  "decimal_places", "acceptance_criterion"]
        widgets = {
            "name": genwidgets.TextInput,
            "description": genwidgets.Textarea,
            "chart_type": genwidgets.Select,
            "subgroup_size": genwidgets.NumberInput,
            "a2": genwidgets.NumberInput,
            "d3": genwidgets.NumberInput,
            "d4": genwidgets.NumberInput,
            "decimal_places": genwidgets.NumberInput,
            "acceptance_criterion": genwidgets.Textarea,
        }


class ControlPointForm(EquipmentScopedFormMixin, GTForm, forms.ModelForm):
    def __init__(self, *args, org_pk=None, **kwargs):
        super().__init__(*args, org_pk=org_pk, **kwargs)
        from laboratory.equipment.serializers import organization_methods

        self.fields["method"].queryset = organization_methods(org_pk)

    class Meta:
        model = ControlPoint
        fields = ["method", "name", "nominal_value", "unit", "reference_standard", "correction",
                  "tolerance", "is_active"]
        widgets = {
            "method": genwidgets.Select,
            "name": genwidgets.TextInput,
            "nominal_value": genwidgets.NumberInput,
            "unit": genwidgets.TextInput,
            "reference_standard": genwidgets.TextInput,
            "correction": genwidgets.NumberInput,
            "tolerance": genwidgets.NumberInput,
            "is_active": genwidgets.YesNoInput,
        }


class ControlMeasurementForm(EquipmentScopedFormMixin, GTForm, forms.ModelForm):
    values = forms.CharField(
        label=_("Readings"), widget=genwidgets.TextInput,
        help_text=_("Separate the readings with a semicolon or a space, e.g. 5.00; 4.99; 5.01"),
    )

    class Meta:
        model = ControlMeasurement
        fields = ["measured_on", "values", "responsible", "observation", "deviation", "corrective_action"]
        widgets = {
            "measured_on": genwidgets.DateInput,
            "responsible": genwidgets.Select,
            "observation": genwidgets.Textarea,
            "deviation": genwidgets.Textarea,
            "corrective_action": genwidgets.Textarea,
        }


class RecalculateLimitsForm(GTForm, forms.Form):
    baseline_from = forms.DateField(label=_("Reference period from"), widget=genwidgets.DateInput)
    baseline_to = forms.DateField(label=_("Reference period to"), widget=genwidgets.DateInput)
    notes = forms.CharField(required=False, label=_("Notes"), widget=genwidgets.Textarea)


class FixedLimitsForm(GTForm, forms.Form):
    """Límites fijos que define el laboratorio (sin período de referencia)."""

    lcl = forms.DecimalField(label=_("Lower control limit"), widget=genwidgets.NumberInput)
    center = forms.DecimalField(label=_("Center line"), widget=genwidgets.NumberInput)
    ucl = forms.DecimalField(label=_("Upper control limit"), widget=genwidgets.NumberInput)
    range_lcl = forms.DecimalField(label=_("Range lower limit"), widget=genwidgets.NumberInput)
    range_center = forms.DecimalField(label=_("Range center line"), widget=genwidgets.NumberInput)
    range_ucl = forms.DecimalField(label=_("Range upper limit"), widget=genwidgets.NumberInput)
    apply_from = forms.DateField(
        required=False, label=_("Apply from"), widget=genwidgets.DateInput,
        help_text=_("Records from this date are evaluated with these limits. Empty: from today"),
    )
    notes = forms.CharField(required=False, label=_("Notes"), widget=genwidgets.Textarea)


class ChartRangeForm(GTForm, forms.Form):
    """Rango de fechas de la carta (GET). Vacío: los últimos registros."""

    date_from = forms.DateField(required=False, label=_("From"), widget=genwidgets.DateInput)
    date_to = forms.DateField(required=False, label=_("To"), widget=genwidgets.DateInput)


class DayControlForm(EquipmentScopedFormMixin, GTForm, forms.Form):
    """Datos comunes del control del día; las lecturas van en un campo por punto."""

    measured_on = forms.DateField(label=_("Date"), widget=genwidgets.DateInput)
    responsible = forms.ModelChoiceField(
        queryset=Profile.objects.none(), required=False, label=_("Responsible"), widget=genwidgets.Select
    )
    observation = forms.CharField(required=False, label=_("Observation"), widget=genwidgets.Textarea)
