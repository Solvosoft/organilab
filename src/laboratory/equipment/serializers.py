from django.conf import settings
from django.utils.translation import gettext_lazy as _
from djgentelella.fields.files import ChunkedFileField
from djgentelella.serializers import GTDateField
from rest_framework import serializers

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
from laboratory.shelfobject.serializers import (
    DateFieldWithEmptyString,
    ValidateShelfobjectEditSerializer,
)
from laboratory.utils import get_actions_by_perms


def org_profiles(org_pk):
    organization = OrganizationStructure.objects.filter(pk=org_pk).first()
    if organization is None:
        return Profile.objects.none()
    return Profile.objects.filter(user__in=organization.users.all())


def record_date(required=True):
    return DateFieldWithEmptyString(
        input_formats=settings.DATE_INPUT_FORMATS, required=required, allow_null=not required
    )


class EquipmentRecordWriteSerializer(ValidateShelfobjectEditSerializer, serializers.ModelSerializer):
    """Base de escritura: organización, laboratorio y equipo validados contra la URL.

    Acota además los perfiles a los usuarios de la organización, los proveedores a los
    del laboratorio y el programa (``plan``) al del mismo equipo.
    """

    profile_fields = ()

    def get_fields(self):
        fields = super().get_fields()
        org_pk = self.context["org_pk"]
        for name in self.profile_fields:
            fields[name].queryset = org_profiles(org_pk)
        if "provider" in fields:
            fields["provider"].queryset = Provider.objects.for_laboratory(org_pk, self.context["lab_pk"])
        if "plan" in fields:
            fields["plan"].queryset = EquipmentActivityPlan.objects.filter(
                shelfobject_id=self.context["shelfobject"]
            )
        return fields


class RecordListSerializer(serializers.ModelSerializer):
    """Fila de datatable con las acciones permitidas al usuario."""

    perms_model = ""
    actions = serializers.SerializerMethodField()

    def get_actions(self, obj):
        from laboratory.api.shelfobject import equipment_record_perms

        return get_actions_by_perms(self.context["request"].user, equipment_record_perms(self.perms_model))


def display(field):
    return serializers.CharField(source=field, read_only=True, default="")


def datatable(row_serializer):
    return type(
        "%sDataTable" % row_serializer.__name__,
        (serializers.Serializer,),
        {
            "data": serializers.ListField(child=row_serializer(), required=True),
            "draw": serializers.IntegerField(required=True),
            "recordsFiltered": serializers.IntegerField(required=True),
            "recordsTotal": serializers.IntegerField(required=True),
        },
    )


def full_name(profile):
    if profile is None:
        return ""
    return profile.user.get_full_name() or profile.user.username


# --- Programa de actividades -------------------------------------------------------

class ActivityPlanWriteSerializer(EquipmentRecordWriteSerializer):
    profile_fields = ("responsible",)
    start_date = record_date(required=False)
    reminder_days_before = serializers.IntegerField(min_value=0, required=False)
    interval_value = serializers.IntegerField(min_value=1)

    class Meta:
        model = EquipmentActivityPlan
        fields = [
            "id", "shelfobject", "organization", "activity_kind", "name", "interval_value",
            "interval_unit", "start_date", "reminder_days_before", "responsible", "is_active", "notes",
        ]


class ActivityPlanRowSerializer(RecordListSerializer):
    perms_model = "equipmentactivityplan"
    activity_kind = display("get_activity_kind_display")
    interval = serializers.SerializerMethodField()
    last_done = serializers.SerializerMethodField()
    next_due = serializers.SerializerMethodField()
    due_status = serializers.SerializerMethodField()
    responsible = serializers.SerializerMethodField()

    def get_interval(self, obj):
        return "%s %s" % (obj.interval_value, obj.get_interval_unit_display().lower())

    def get_last_done(self, obj):
        value = obj.last_done()
        return value.strftime("%d/%m/%Y") if value else ""

    def get_next_due(self, obj):
        value = obj.next_due()
        return value.strftime("%d/%m/%Y") if value else ""

    def get_due_status(self, obj):
        if not obj.is_active:
            return {"code": "inactive", "text": str(_("Inactive"))}
        status = obj.due_status()
        texts = {
            EquipmentActivityPlan.VALID: _("Up to date"),
            EquipmentActivityPlan.DUE_SOON: _("Due soon"),
            EquipmentActivityPlan.EXPIRED: _("Expired"),
        }
        return {"code": status, "text": str(texts[status])}

    def get_responsible(self, obj):
        return full_name(obj.responsible)

    class Meta:
        model = EquipmentActivityPlan
        fields = [
            "id", "activity_kind", "name", "interval", "last_done", "next_due", "due_status",
            "responsible", "is_active", "actions",
        ]


class ActivityPlanValuesSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(format="%d/%m/%Y")

    class Meta:
        model = EquipmentActivityPlan
        fields = ActivityPlanWriteSerializer.Meta.fields


# --- Verificaciones intermedias ------------------------------------------------------

class VerificationWriteSerializer(EquipmentRecordWriteSerializer):
    profile_fields = ("responsible",)
    verification_date = record_date()
    document = ChunkedFileField(required=False, allow_empty_file=True, allow_null=True)

    class Meta:
        model = ShelfObjectVerification
        fields = [
            "id", "shelfobject", "organization", "plan", "verification_date", "verification_type",
            "result", "acceptance_criterion", "conformity", "responsible", "document", "observation",
        ]


class VerificationRowSerializer(RecordListSerializer):
    perms_model = "shelfobjectverification"
    verification_date = GTDateField()
    conformity = display("get_conformity_display")
    responsible = serializers.SerializerMethodField()
    document = ChunkedFileField(read_only=True)

    def get_responsible(self, obj):
        return full_name(obj.responsible)

    class Meta:
        model = ShelfObjectVerification
        fields = [
            "id", "verification_date", "verification_type", "result", "conformity", "responsible",
            "document", "actions",
        ]


class VerificationValuesSerializer(serializers.ModelSerializer):
    verification_date = serializers.DateField(format="%d/%m/%Y")

    class Meta:
        model = ShelfObjectVerification
        exclude = ["document"]


# --- Fallas y reparaciones -------------------------------------------------------------

class FailureWriteSerializer(EquipmentRecordWriteSerializer):
    profile_fields = ("responsible",)
    failure_date = record_date()
    return_to_service_date = record_date(required=False)
    report = ChunkedFileField(required=False, allow_empty_file=True, allow_null=True)

    class Meta:
        model = ShelfObjectFailure
        fields = [
            "id", "shelfobject", "organization", "failure_date", "description", "blocked",
            "repair_done", "modifications", "provider", "responsible", "return_to_service_date",
            "verification_before_use", "impact_assessment", "report",
        ]

    def validate(self, data):
        data = super().validate(data)
        returned = data.get("return_to_service_date")
        if returned and returned < data["failure_date"]:
            raise serializers.ValidationError(
                {"return_to_service_date": _("The return to service cannot be before the failure.")}
            )
        return data


class FailureRowSerializer(RecordListSerializer):
    perms_model = "shelfobjectfailure"
    failure_date = GTDateField()
    return_to_service_date = GTDateField()
    provider = display("provider.name")
    report = ChunkedFileField(read_only=True)

    class Meta:
        model = ShelfObjectFailure
        fields = [
            "id", "failure_date", "description", "blocked", "repair_done", "provider",
            "return_to_service_date", "report", "actions",
        ]


class FailureValuesSerializer(serializers.ModelSerializer):
    failure_date = serializers.DateField(format="%d/%m/%Y")
    return_to_service_date = serializers.DateField(format="%d/%m/%Y")

    class Meta:
        model = ShelfObjectFailure
        exclude = ["report"]


# --- Documentos --------------------------------------------------------------------------

class DocumentWriteSerializer(EquipmentRecordWriteSerializer):
    valid_from = record_date(required=False)
    file = ChunkedFileField(required=True)

    class Meta:
        model = EquipmentDocument
        fields = [
            "id", "shelfobject", "organization", "document_type", "title", "version", "file",
            "valid_from",
        ]

    def get_fields(self):
        fields = super().get_fields()
        if self.instance is not None:
            # Al editar, conservar el archivo si no se sube otro.
            fields["file"].required = False
        return fields


class DocumentRowSerializer(RecordListSerializer):
    perms_model = "equipmentdocument"
    document_type = display("document_type.description")
    valid_from = GTDateField()
    file = ChunkedFileField(read_only=True)

    class Meta:
        model = EquipmentDocument
        fields = ["id", "document_type", "title", "version", "valid_from", "file", "actions"]


class DocumentValuesSerializer(serializers.ModelSerializer):
    valid_from = serializers.DateField(format="%d/%m/%Y")

    class Meta:
        model = EquipmentDocument
        exclude = ["file"]


# --- Cartas de control (F3) ----------------------------------------------------------

def organization_methods(org_pk):
    organization = OrganizationStructure.objects.filter(pk=org_pk).first()
    if organization is None:
        return ControlMethod.objects.none()
    return ControlMethod.objects.filter(organization__in=organization.ancestors(include_self=True))


class ControlMethodWriteSerializer(serializers.ModelSerializer):
    a2 = serializers.DecimalField(max_digits=8, decimal_places=4, required=False, allow_null=True)
    d3 = serializers.DecimalField(max_digits=8, decimal_places=4, required=False, allow_null=True)
    d4 = serializers.DecimalField(max_digits=8, decimal_places=4, required=False, allow_null=True)

    def validate(self, data):
        chart = data.get("chart_type", getattr(self.instance, "chart_type", ControlMethod.XBAR_R))
        n = data.get("subgroup_size", getattr(self.instance, "subgroup_size", 5))
        if chart == ControlMethod.XBAR_R and not 2 <= n <= 10:
            raise serializers.ValidationError(
                {"subgroup_size": _("A means and ranges chart needs between 2 and 10 readings per record.")}
            )
        return data

    class Meta:
        model = ControlMethod

        fields = ["id", "name", "description", "chart_type", "subgroup_size", "a2", "d3", "d4",
                  "decimal_places", "acceptance_criterion"]


class ControlMethodRowSerializer(RecordListSerializer):
    perms_model = "controlmethod"
    chart_type = display("get_chart_type_display")
    organization = display("organization.name")

    class Meta:
        model = ControlMethod

        fields = ["id", "name", "chart_type", "subgroup_size", "a2", "d3", "d4", "organization", "actions"]


class ControlMethodValuesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControlMethod

        fields = ControlMethodWriteSerializer.Meta.fields


class ControlPointWriteSerializer(EquipmentRecordWriteSerializer):
    def get_fields(self):
        fields = super().get_fields()
        fields["method"].queryset = organization_methods(self.context["org_pk"])
        return fields

    class Meta:
        model = ControlPoint

        fields = ["id", "shelfobject", "organization", "method", "name", "nominal_value", "unit",
                  "reference_standard", "correction", "tolerance", "is_active"]


class ControlPointRowSerializer(RecordListSerializer):
    perms_model = "controlpoint"
    method = display("method.name")
    limits = serializers.SerializerMethodField()
    last_record = serializers.SerializerMethodField()
    chart_url = serializers.SerializerMethodField()

    def get_limits(self, obj):
        limits = obj.current_limits()
        if limits is None:
            return ""
        return "%s / %s / %s" % tuple(
            format(value.normalize(), "f") for value in (limits.lcl, limits.center, limits.ucl)
        )

    def get_last_record(self, obj):
        record = obj.controlmeasurement_set.order_by("-measured_on", "-pk").first()
        if record is None:
            return {"text": "", "alert": False}
        return {"text": record.measured_on.strftime("%d/%m/%Y"),
                "alert": record.out_of_control or record.out_of_acceptance}

    def get_chart_url(self, obj):
        from django.urls import reverse

        view = self.context["view"]
        return reverse("laboratory:equipment_control_point", kwargs={
            "org_pk": view.kwargs["org_pk"], "lab_pk": view.kwargs["lab_pk"],
            "pk": view.kwargs["shelfobject"], "point": obj.pk,
        })

    class Meta:
        model = ControlPoint

        fields = ["id", "name", "method", "nominal_value", "unit", "correction", "tolerance", "limits",
                  "last_record", "chart_url", "is_active", "actions"]


class ControlPointValuesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControlPoint

        exclude = ["created_by", "creation_date", "last_update"]


class ReadingsField(serializers.Field):
    """Lecturas como lista o como texto «5.00; 4,99 5.01» (punto y coma, espacio o salto de línea).

    La coma no separa lecturas: puede ser la coma decimal.
    """

    def to_internal_value(self, data):
        import re

        if isinstance(data, str):
            data = [part for part in re.split(r"[;\s]+", data.strip()) if part]
        if not isinstance(data, list) or not data:
            raise serializers.ValidationError(_("Enter the readings."))
        return [str(value).strip().replace(",", ".") for value in data]

    def to_representation(self, value):
        return "; ".join(value or [])


class ControlMeasurementWriteSerializer(EquipmentRecordWriteSerializer):
    profile_fields = ("responsible",)
    measured_on = record_date()
    values = ReadingsField()

    def get_fields(self):
        fields = super().get_fields()
        # Valida el equipo de la URL, pero el registro cuelga del punto, no del equipo.
        fields["shelfobject"].write_only = True
        return fields

    class Meta:
        model = ControlMeasurement

        fields = ["id", "shelfobject", "organization", "measured_on", "values", "responsible", "observation",
                  "deviation", "corrective_action"]


class ControlMeasurementRowSerializer(RecordListSerializer):
    perms_model = "controlmeasurement"
    measured_on = GTDateField()
    responsible = serializers.SerializerMethodField()
    values = serializers.SerializerMethodField()
    mean = serializers.SerializerMethodField()
    range = serializers.SerializerMethodField()
    corrected_mean = serializers.SerializerMethodField()

    def number(self, obj, value):
        """Con los decimales del método de control (sin ceros de relleno de la base)."""
        if value is None:
            return ""
        return "{:.{places}f}".format(value, places=obj.point.method.decimal_places)

    def get_mean(self, obj):
        return self.number(obj, obj.mean)

    def get_range(self, obj):
        return self.number(obj, obj.range)

    def get_corrected_mean(self, obj):
        return self.number(obj, obj.corrected_mean)

    def get_responsible(self, obj):
        return full_name(obj.responsible)

    def get_values(self, obj):
        return ", ".join(obj.values or [])

    class Meta:
        model = ControlMeasurement

        fields = ["id", "measured_on", "values", "mean", "range", "corrected_mean", "out_of_control",
                  "out_of_acceptance", "responsible", "observation", "deviation", "corrective_action", "actions"]


class ControlMeasurementValuesSerializer(serializers.ModelSerializer):
    measured_on = serializers.DateField(format="%d/%m/%Y")
    values = ReadingsField()

    class Meta:
        model = ControlMeasurement

        fields = ["id", "measured_on", "values", "responsible", "observation", "deviation", "corrective_action"]


class RecalculateLimitsSerializer(serializers.Serializer):
    baseline_from = record_date()
    baseline_to = record_date()
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, data):
        if data["baseline_from"] > data["baseline_to"]:
            raise serializers.ValidationError({"baseline_to": _("The end of the period must be after its start.")})
        return data
