import json

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from djgentelella.fields.files import ChunkedFileField
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.files import FileChunkedUpload
from rest_framework import serializers

from auth_and_perms.models import Profile
from laboratory.equipment.importer import INVENTORY, PROGRAM
from laboratory.models import Shelf, ShelfObjectCalibrate

KINDS = (
    (INVENTORY, _("Equipment inventory (one header row)")),
    (PROGRAM, _("Equipment program PT-05 R-10 (calibration and maintenance)")),
)


class ShelfChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, shelf):
        return "%s / %s / %s" % (shelf.furniture.labroom, shelf.furniture, shelf)


class EquipmentImportForm(GTForm, forms.Form):
    file = forms.FileField(widget=FileChunkedUpload, label=_("Spreadsheet (.xlsx)"))
    kind = forms.ChoiceField(choices=KINDS, label=_("Format"), widget=genwidgets.Select)
    sheet = forms.CharField(
        required=False, label=_("Sheet"), widget=genwidgets.TextInput,
        help_text=_("Leave empty to use the sheet with the most recognized rows."),
    )
    shelf = ShelfChoiceField(
        queryset=Shelf.objects.none(), label=_("Destination shelf"), widget=genwidgets.Select,
        help_text=_("New equipment is placed here; the spreadsheet location is kept as the specific physical location."),
    )

    def __init__(self, *args, laboratory=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["shelf"].queryset = Shelf.objects.filter(
            furniture__labroom__laboratory=laboratory
        ).select_related("furniture__labroom").order_by("furniture__labroom__name", "furniture__name", "name")


class EquipmentImportFileSerializer(serializers.Serializer):
    """Convierte el token de ``FileChunkedUpload`` en el archivo subido."""

    file = ChunkedFileField(required=True, allow_empty_file=False)

    def validate_file(self, value):
        name = (getattr(value, "name", "") or "").lower()
        if not name.endswith((".xlsx", ".xlsm")):
            raise serializers.ValidationError(_("Only .xlsx or .xlsm files are allowed."))
        return value


def text_field(label, required=False):
    return forms.CharField(
        required=required, label=label, max_length=255,
        widget=genwidgets.TextInput(attrs={"class": "form-control form-control-sm"}),
    )


def date_field(label):
    # Día/mes/año como el resto del proyecto: con el idioma en inglés, el DateField
    # probaría primero mes/día y 10/04 sería el 4 de octubre.
    return forms.DateField(
        required=False, label=label, widget=genwidgets.DateInput, input_formats=settings.DATE_INPUT_FORMATS
    )


class EquipmentImportRowForm(forms.Form):
    """Una fila del Excel tal como se va a importar; todo es corregible."""

    VISIBLE_INVENTORY = (
        "include", "internal_code", "name", "brand", "model", "serial_number", "asset_number",
        "physical_location", "responsible", "custodian", "decommissioned",
    )
    VISIBLE_PROGRAM = VISIBLE_INVENTORY + (
        "calibration_date", "next_calibration_date", "calibration_conformity", "maintenance_date",
    )

    include = forms.BooleanField(required=False, initial=True, label=_("Import"))
    internal_code = text_field(_("Internal code"), required=True)
    name = text_field(_("Equipment"), required=True)
    brand = text_field(_("Brand"))
    model = text_field(_("Model"))
    serial_number = text_field(_("Serial number"))
    asset_number = text_field(_("Asset number"))
    physical_location = text_field(_("Location"))
    responsible = forms.CharField(required=False, widget=forms.HiddenInput)
    custodian = forms.ModelChoiceField(
        queryset=Profile.objects.none(), required=False, label=_("Responsible / custodian"),
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    decommissioned = forms.BooleanField(required=False, label=_("Decommissioned"))
    notes = forms.CharField(required=False, widget=forms.HiddenInput)
    magnitude = forms.CharField(required=False, widget=forms.HiddenInput)
    measurement_unit = forms.CharField(required=False, widget=forms.HiddenInput)
    resolution = forms.CharField(required=False, widget=forms.HiddenInput)
    working_range = forms.CharField(required=False, widget=forms.HiddenInput)
    software_version = forms.CharField(required=False, widget=forms.HiddenInput)
    authorized_users = forms.CharField(required=False, widget=forms.HiddenInput)
    calibration_date = date_field(_("Calibration date"))
    next_calibration_date = date_field(_("Next calibration"))
    calibration_conformity = forms.ChoiceField(
        required=False, label=_("Conformity"), choices=(("", "---"),) + ShelfObjectCalibrate.CONFORMITY,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    calibration_result = forms.CharField(required=False, widget=forms.HiddenInput)
    maintenance = forms.CharField(required=False, widget=forms.HiddenInput)
    maintenance_date = date_field(_("Maintenance executed on"))

    def __init__(self, *args, profiles=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["custodian"].queryset = profiles if profiles is not None else Profile.objects.none()

    def clean_maintenance(self):
        raw = self.cleaned_data.get("maintenance") or "[]"
        try:
            value = json.loads(raw)
        except ValueError:
            raise forms.ValidationError(_("Invalid maintenance data."))
        return value if isinstance(value, list) else []

    def clean(self):
        data = super().clean()
        calibration, next_calibration = data.get("calibration_date"), data.get("next_calibration_date")
        if calibration and next_calibration and next_calibration <= calibration:
            self.add_error("next_calibration_date", _("The next calibration must be after the calibration date."))
        if data.get("maintenance_date") and not any(block.get("executed") for block in data.get("maintenance") or []):
            self.add_error("maintenance_date", _("The spreadsheet does not register an executed maintenance for this equipment."))
        return data

    def as_row(self):
        """La fila para el importador: fechas en ISO y el perfil por pk."""
        data = dict(self.cleaned_data)
        for name in ("calibration_date", "next_calibration_date", "maintenance_date"):
            data[name] = data[name].isoformat() if data.get(name) else ""
        data["custodian"] = data["custodian"].pk if data.get("custodian") else None
        return data


def row_initial(row, matcher):
    """Datos iniciales de una fila leída del Excel, con el responsable ya resuelto."""
    import datetime

    initial = dict(row)
    initial["include"] = True
    initial["maintenance"] = json.dumps(row.get("maintenance") or [])
    initial["custodian"] = matcher.match(row.get("responsible"))
    for name in ("calibration_date", "next_calibration_date"):
        initial[name] = datetime.date.fromisoformat(row[name]) if row.get(name) else None
    return initial
