from django import forms
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.selects import AutocompleteSelectMultiple, AutocompleteSelect

from auth_and_perms.models import Profile
from laboratory.models import (
    Laboratory,
    Furniture,
    LaboratoryRoom,
    Object,
    ObjectLogChange,
    PrecursorReportValues,
)
from laboratory.utils import (
    get_laboratories_from_organization,
    get_users_from_organization,
)
from report.models import TaskReport, DocumentReportStatus
from risk_management.models import RiskZone, Buildings


def get_years():
    years = [
        (i, i)
        for i in ObjectLogChange.objects.all()
        .values_list("update_time__year", flat=True)
        .distinct()
        .order_by("update_time__year")
    ]
    return years


class ReportBase(GTForm, forms.ModelForm):
    name = forms.CharField(
        max_length=100,
        label=_("File Name"),
        widget=genwidgets.TextInput(),
        required=True,
    )
    title = forms.CharField(
        max_length=100,
        label=_("Report Title"),
        widget=genwidgets.TextInput(),
        required=True,
    )
    organization = forms.IntegerField(widget=forms.HiddenInput())
    report_name = forms.CharField(widget=forms.HiddenInput())
    format = forms.ChoiceField(
        widget=genwidgets.Select,
        choices=(
            ("html", _("On screen")),
            ("pdf", _("PDF")),
            ("xls", "XLS"),
            ("xlsx", "XLSX"),
            ("ods", "ODS"),
        ),
        required=False,
        label=_("Format"),
    )

    def clean_name(self):
        name = self.cleaned_data["name"]
        name = slugify(name)
        return name


class ReportForm(ReportBase):
    laboratory = forms.ModelMultipleChoiceField(
        widget=AutocompleteSelectMultiple(
            "labs_by_org",
            attrs={
                "data-related": "true",
                "data-pos": 0,
                "data-groupname": "lab_by_org",
                "data-s2filter-organization": "#id_organization",
            },
        ),
        queryset=Laboratory.objects.all(),
        required=False,
        label=_("Laboratory"),
    )

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop("org_pk", None)
        super(ReportForm, self).__init__(*args, **kwargs)

        if org_pk:
            lab_ids = get_laboratories_from_organization(org_pk)
            self.fields["laboratory"].queryset = Laboratory.objects.filter(
                pk__in=lab_ids
            )

    def clean_laboratory(self):
        organization = self.cleaned_data["organization"]
        laboratory = self.cleaned_data["laboratory"]

        if not laboratory:
            laboratory = get_laboratories_from_organization(organization)

        return list(laboratory.values_list("pk", flat=True))


class ReportSimpleForm(ReportBase):
    laboratory = forms.ModelChoiceField(
        widget=AutocompleteSelect(
            "labs_by_org",
            attrs={
                "data-related": "true",
                "data-pos": 0,
                "data-groupname": "lab_by_org",
                "data-s2filter-organization": "#id_organization",
            },
        ),
        queryset=Laboratory.objects.all(),
        required=True,
        label=_("Laboratory"),
    )

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop("org_pk", None)
        super(ReportSimpleForm, self).__init__(*args, **kwargs)

        if org_pk:
            lab_ids = get_laboratories_from_organization(org_pk)
            self.fields["laboratory"].queryset = Laboratory.objects.filter(
                pk__in=lab_ids
            )

    def clean(self):
        cleaned = super().clean()
        lab = cleaned.get("laboratory")
        if lab is not None:
            cleaned["laboratory"] = [lab.pk]
        return cleaned


class ReportObjectsBaseForm(ReportBase):
    object_type = forms.CharField(
        max_length=1, widget=genwidgets.HiddenInput(), required=False
    )


class LaboratoryRoomReportForm(ReportForm):
    objects_type = list(Object.TYPE_CHOICES)
    objects_type.insert(0, (None, _("All")))

    object_type = forms.ChoiceField(
        choices=tuple(objects_type),
        label=_("Object type"),
        required=False,
        widget=genwidgets.Select(attrs={"class": "form-control"}),
    )
    is_precursor = forms.BooleanField(
        widget=genwidgets.YesNoInput, required=False, label=_("Is precursor?")
    )
    lab_room = forms.ModelMultipleChoiceField(
        help_text=_(
            "If you want to delimit this query select laboratory rooms (Optional)"
        ),
        widget=AutocompleteSelectMultiple(
            "lab_room_ref",
            attrs={
                "data-related": "true",
                "data-pos": 1,
                "data-groupname": "lab_by_org",
                "data-s2filter-organization": "#id_organization",
                "data-s2filter-laboratory": "#id_laboratory",
            },
        ),
        queryset=LaboratoryRoom.objects.all(),
        label=_("Filter Laboratory Room"),
        required=False,
    )
    furniture = forms.ModelMultipleChoiceField(
        help_text=_("If you want to delimit this query select furnitures (Optional)"),
        widget=AutocompleteSelectMultiple(
            "furniture_ref",
            attrs={
                "data-related": "true",
                "data-pos": 2,
                "data-groupname": "lab_by_org",
                "data-s2filter-organization": "#id_organization",
                "data-s2filter-laboratory": "#id_laboratory",
            },
        ),
        queryset=Furniture.objects.all(),
        label=_("Filter Furniture"),
        required=False,
    )


class ValidateLaboratoryRoomReportForm(ReportForm):
    lab_room = forms.ModelMultipleChoiceField(
        widget=genwidgets.SelectMultiple,
        queryset=LaboratoryRoom.objects.all(),
        required=False,
    )
    furniture = forms.ModelMultipleChoiceField(
        widget=genwidgets.SelectMultiple,
        queryset=Furniture.objects.all(),
        required=False,
    )
    objects_type = list(Object.TYPE_CHOICES)
    objects_type.insert(0, (None, _("All")))
    object_type = forms.ChoiceField(
        choices=tuple(objects_type),
        required=False,
        widget=genwidgets.Select(attrs={"class": "form-control"}),
    )
    is_precursor = forms.BooleanField(widget=genwidgets.YesNoInput, required=False)

    def clean_lab_room(self):

        lab_room = self.cleaned_data["lab_room"]
        laboratory = self.cleaned_data["laboratory"]

        if lab_room:
            lab_room = LaboratoryRoom.objects.filter(pk__in=lab_room)
        else:
            lab_room = LaboratoryRoom.objects.filter(laboratory__in=laboratory)

        return list(lab_room.values_list("pk", flat=True).distinct())

    def get_furniture(self, lab_room, laboratory):
        furniture = Furniture.objects.filter(labroom__laboratory__in=list(laboratory))
        if lab_room:
            furniture = furniture.filter(labroom__in=lab_room)
        furniture = furniture.distinct()
        return furniture

    def clean_furniture(self):
        lab_room = self.cleaned_data["lab_room"]
        furniture = self.cleaned_data["furniture"]
        laboratory = self.cleaned_data["laboratory"]

        if not furniture:
            furniture = self.get_furniture(lab_room, laboratory)
        else:
            furniture = self.get_furniture(lab_room, laboratory)

        return list(furniture.values_list("pk", flat=True).distinct())

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop("org_pk", None)
        super(ValidateLaboratoryRoomReportForm, self).__init__(*args, **kwargs)


class ObjectLogChangeBaseForm(ReportSimpleForm):
    period = forms.CharField(
        widget=genwidgets.DateRangeInput, required=False, label=_("Period")
    )
    precursor = forms.BooleanField(
        widget=genwidgets.YesNoInput, required=False, label=_("Precursor")
    )
    resume = forms.BooleanField(
        widget=genwidgets.YesNoInput, required=False, label=_("Resume")
    )


class OrganizationReactiveForm(ReportBase):
    users = forms.ModelMultipleChoiceField(
        help_text=_("If you want to delimit this query select users (Optional)"),
        widget=genwidgets.SelectMultiple(),
        queryset=Profile.objects.all(),
        label=_("Filter User"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop("org_pk", None)
        super(OrganizationReactiveForm, self).__init__(*args, **kwargs)

        if org_pk:
            self.fields["users"].queryset = Profile.objects.filter(
                user__in=get_users_from_organization(org_pk)
            )

    def clean_user(self):
        organization = self.cleaned_data["organization"]
        users = self.cleaned_data["users"]

        if not users:
            users = get_users_from_organization(organization)

        return list(users.values_list("pk", flat=True))

    def clean_users(self):
        organization = self.cleaned_data["organization"]
        users = self.cleaned_data["users"]

        if not users:
            users = get_users_from_organization(organization)
        else:
            users = users.values_list("user__pk", flat=True)
        return list(users.distinct())


class ValidateObjectTypeForm(GTForm):
    type_id = forms.CharField(max_length=1)

    def clean_type_id(self):
        type_id = self.cleaned_data.get("type_id")
        if type_id:
            if type_id not in dict(Object.TYPE_CHOICES).keys():
                self.add_error("type_id", _("Object type is not allowed"))
            return type_id
        else:
            return None


class ValidateFurnitureForm(GTForm):
    organization = forms.IntegerField(required=False)
    furniture = forms.IntegerField()
    laboratory = forms.ModelMultipleChoiceField(
        queryset=Laboratory.objects.all(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop("org_pk", None)
        super(ValidateFurnitureForm, self).__init__(*args, **kwargs)

        if org_pk:
            self.fields["organization"].initial = org_pk
            lab_ids = get_laboratories_from_organization(org_pk)
            self.fields["laboratory"].queryset = Laboratory.objects.filter(
                pk__in=lab_ids
            )

    def clean_organization(self):
        org = (
            self.cleaned_data.get("organization") or self.fields["organization"].initial
        )
        if not org:
            raise forms.ValidationError(_("Organization is required"))
        return int(org)

    def clean_laboratory(self):
        organization = self.cleaned_data["organization"]
        laboratory = self.cleaned_data["laboratory"]

        if not laboratory:
            laboratory = get_laboratories_from_organization(organization)

        return list(laboratory.values_list("pk", flat=True))

    def clean(self):
        cleaned_data = super().clean()
        labs = cleaned_data.get("laboratory")
        furniture = cleaned_data.get("furniture")

        if not furniture or not labs:
            self.add_error("furniture", _("Furniture is not allowed"))
            return cleaned_data

        furniture_obj = Furniture.objects.filter(
            pk=furniture, labroom__laboratory__in=labs
        )

        if not furniture_obj.exists():
            self.add_error("furniture", _("Furniture is not allowed"))

        return cleaned_data


class TasksForm(GTForm):
    task = forms.CharField(max_length=255)
    taskreport = forms.IntegerField()

    def clean_taskreport(self):
        taskreport = self.cleaned_data.get("taskreport", 0)
        report = TaskReport.objects.filter(pk=taskreport)

        if not report.exists():
            self.add_error("taskreport", _("Task report doesn't exists"))
        return taskreport


class DiscardShelfForm(ReportForm):

    period = forms.CharField(
        widget=genwidgets.DateRangeInput, required=False, label=_("Period")
    )


class RiskZoneReportForm(ReportForm):
    risk_zone = forms.ModelMultipleChoiceField(
        widget=genwidgets.SelectMultiple,
        queryset=RiskZone.objects.all(),
        label=_("Risk Zones"),
        required=False,
    )
    building = forms.ModelMultipleChoiceField(
        widget=genwidgets.SelectMultiple,
        queryset=Buildings.objects.all(),
        label=_("Buildings"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop("org_pk", None)
        super(RiskZoneReportForm, self).__init__(*args, **kwargs)

        if org_pk:
            self.fields["risk_zone"].queryset = RiskZone.objects.filter(
                organization=org_pk
            )
            self.fields["building"].queryset = Buildings.objects.filter(
                organization=org_pk
            )

    def clean_building(self):
        building = self.cleaned_data["building"]

        if building.exists():
            return list(building.values_list("pk", flat=True))
        return []

    def clean_risk_zone(self):
        risk_zone = self.cleaned_data["risk_zone"]
        if risk_zone.exists():
            return list(risk_zone.values_list("pk", flat=True))
        return []


class ReactiveStockReportForm(ReportForm):
    format = forms.ChoiceField(
        widget=genwidgets.Select,
        choices=(
            ("xlsx", "XLSX"),
            ("ods", "ODS"),
        ),
        required=False,
        label=_("Format"),
    )


class RegencyReportForm(ReportForm):

    years = forms.ChoiceField(
        widget=genwidgets.Select,
        choices=[],
        required=True,
        label=_("Year"),
    )

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop("org_pk", None)
        super(RegencyReportForm, self).__init__(*args, **kwargs)

        if org_pk:
            lab_ids = get_laboratories_from_organization(org_pk)
            self.fields["laboratory"].queryset = Laboratory.objects.filter(
                pk__in=lab_ids
            )

        self.fields["years"].choices = get_years()
        self.fields["format"].choices = (
            ("xls", "XLS"),
            ("xlsx", "XLSX"),
            ("ods", "ODS"),
        )


class CompatibilityReportForm(ReportBase):
    format = forms.ChoiceField(
        widget=genwidgets.Select,
        choices=(
            ("html", _("On screen")),
            ("pdf", _("PDF")),
            ("ods", "ODS"),
        ),
        required=False,
        label=_("Format"),
    )
    risk_zone = forms.ModelMultipleChoiceField(
        widget=genwidgets.SelectMultiple,
        queryset=RiskZone.objects.all(),
        label=_("Risk Zones"),
        required=False,
    )
    building = forms.ModelMultipleChoiceField(
        widget=genwidgets.SelectMultiple,
        queryset=Buildings.objects.all(),
        label=_("Buildings"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop("org_pk", None)
        super(CompatibilityReportForm, self).__init__(*args, **kwargs)

        if org_pk:
            self.fields["risk_zone"].queryset = RiskZone.objects.filter(
                organization=org_pk
            )
            self.fields["building"].queryset = Buildings.objects.filter(
                organization=org_pk
            )

    def clean_building(self):
        building = self.cleaned_data["building"]
        if building.exists():
            return list(building.values_list("pk", flat=True))
        return []

    def clean_risk_zone(self):
        risk_zone = self.cleaned_data["risk_zone"]
        if risk_zone.exists():
            return list(risk_zone.values_list("pk", flat=True))
        return []


class HazardMapReportForm(ReportBase):
    format = forms.ChoiceField(
        widget=genwidgets.Select,
        choices=(
            ("html", _("On screen")),
            ("pdf", _("PDF")),
        ),
        required=False,
        label=_("Format"),
    )
    laboratory = forms.ModelMultipleChoiceField(
        widget=AutocompleteSelectMultiple(
            "labs_by_org",
            attrs={
                "data-related": "true",
                "data-pos": 0,
                "data-groupname": "lab_by_org",
                "data-s2filter-organization": "#id_organization",
            },
        ),
        queryset=Laboratory.objects.all(),
        label=_("Laboratories"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop("org_pk", None)
        super(HazardMapReportForm, self).__init__(*args, **kwargs)

        if org_pk:
            lab_ids = get_laboratories_from_organization(org_pk)
            self.fields["laboratory"].queryset = Laboratory.objects.filter(
                pk__in=lab_ids
            )

    def clean_laboratory(self):
        organization = self.cleaned_data["organization"]
        laboratory = self.cleaned_data["laboratory"]

        if not laboratory:
            laboratory = get_laboratories_from_organization(organization)

        return list(laboratory.values_list("pk", flat=True))


class PrecursorFilterForm(GTForm):
    organization = forms.IntegerField(
        required=True,
        widget=forms.HiddenInput(),
    )

    laboratory = forms.ModelChoiceField(
        widget=AutocompleteSelect(
            "labs_by_org",
            attrs={
                "data-related": "true",
                "data-pos": 0,
                "data-groupname": "lab_by_org",
                "data-s2filter-organization": "#id_organization",
            },
        ),
        queryset=Laboratory.objects.all(),
        required=True,
        label=_("Laboratory"),
    )

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop("org_pk", None)
        super().__init__(*args, **kwargs)

        if not org_pk:
            return

        if org_pk:
            self.fields["organization"].initial = org_pk
            lab_ids = get_laboratories_from_organization(org_pk)
            self.fields["laboratory"].queryset = Laboratory.objects.filter(
                pk__in=lab_ids
            )


class PrecursorReportValuesViewForm(GTForm, forms.ModelForm):

    default_render_type = "as_grid"

    grid_representation = [
        [["object"], ["measurement_unit"]],
        [["quantity"], ["previous_balance"], ["new_income"]],
        [["month_expense"], ["final_balance"], ["stock"]],
        [["bills"], ["providers"]],
        [
            ["reason_to_spend"],
        ],
    ]

    object = forms.ModelChoiceField(
        queryset=Object.objects.filter(
            type=0,
            sustancecharacteristics__is_precursor=True,
        ),
        required=True,
        widget=genwidgets.Select,
        label=_("Object"),
    )

    def __init__(self, *args, **kwargs):
        precusor_pk = kwargs.pop("precusor_pk", None)
        org_pk = kwargs.pop("org_pk", None)
        super(PrecursorReportValuesViewForm, self).__init__(*args, **kwargs)

        if org_pk:
            self.fields["object"].queryset = Object.objects.filter(
                organization__pk=org_pk,
                type=0,
                sustancecharacteristics__is_precursor=True,
            )

    class Meta:
        model = PrecursorReportValues
        fields = [
            "precursor_report",
            "object",
            "measurement_unit",
            "quantity",
            "previous_balance",
            "new_income",
            "bills",
            "providers",
            "stock",
            "month_expense",
            "final_balance",
            "reason_to_spend",
        ]
        widgets = {
            "measurement_unit": genwidgets.Select,
            "quantity": genwidgets.NumberInput,
            "previous_balance": genwidgets.NumberInput,
            "new_income": genwidgets.NumberInput,
            "bills": genwidgets.TextInput,
            "providers": genwidgets.TextInput,
            "stock": genwidgets.NumberInput,
            "month_expense": genwidgets.NumberInput,
            "final_balance": genwidgets.NumberInput,
            "reason_to_spend": genwidgets.Textarea,
        }
