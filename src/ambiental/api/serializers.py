from django.db.models import Q
from django.utils import formats
from django.utils.translation import gettext_lazy as _
from djgentelella.fields.files import ChunkedFileField
from djgentelella.serializers import GTDateField
from djgentelella.serializers.selects import GTS2SerializerBase
from rest_framework import serializers

from ambiental.ambiental_defaults import (
    EXTRA_FIELDS,
    KEY_MEASURE_UNIT,
    KEY_NORMALIZER,
    KEY_POINT_TYPE,
    KEY_RESOURCE_TYPE,
    KEY_WASTE_TREATMENT,
    get_resource_info,
)
from ambiental.models import ConsumptionAlert, ConsumptionRecord, MeasurementPoint, NormalizationBase
from laboratory.models import Catalog, Laboratory, Provider
from presentation.parameters import get_parameter
from risk_management.models import Buildings


def date_field(**kwargs):
    """Un ``GTDateField`` con el formato del idioma de **esta** petición.

    ``GTDateField`` resuelve su formato al instanciarse; declarado como atributo de
    clase queda congelado con el idioma activo al importar el módulo, y un usuario con
    otro idioma recibiría fechas que su propio formulario no sabe devolver. Además
    acepta ISO 8601, que es lo que manda cualquier cliente de API.
    """
    return GTDateField(
        input_formats=[formats.get_format("DATE_INPUT_FORMATS")[0], "%Y-%m-%d"],
        **kwargs,
    )


def actions_for(serializer, model_name, building, extra_perms=None):
    """Acciones de fila que el datatable muestra u oculta, según el rol en ese edificio."""
    access = serializer.context.get("building_access")
    perms = {
        "update": "ambiental.change_%s" % model_name,
        "destroy": "ambiental.delete_%s" % model_name,
    }
    perms.update(extra_perms or {})
    if access is None:
        user = serializer.context["request"].user
        return {action: user.has_perm(perm) for action, perm in perms.items()}
    return {action: access.has(perm, building) for action, perm in perms.items()}


class DataTableSerializer(serializers.Serializer):
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class OrganizationScopedSerializer(serializers.ModelSerializer):
    """Acota los querysets de las relaciones a la organización de la URL."""

    def get_organization(self):
        return self.context.get("organization")

    def visible_buildings(self, organization, perm):
        """Edificios que el usuario puede ver: los demás ni se ofrecen ni se aceptan."""
        access = self.context.get("building_access")
        if access is None:
            return Buildings.objects.filter(organization=organization)
        return access.buildings(perm)

    def scope_fields(self, fields, organization):
        pass

    def get_fields(self):
        fields = super().get_fields()
        organization = self.get_organization()
        if organization is not None:
            self.scope_fields(fields, organization)
        return fields


# ---------------------------------------------------------------------------
# Puntos de medición
# ---------------------------------------------------------------------------


class MeasurementPointSerializer(serializers.ModelSerializer):
    point_type = GTS2SerializerBase()
    resource_type = GTS2SerializerBase()
    building = GTS2SerializerBase()
    laboratories = GTS2SerializerBase(many=True)
    actions = serializers.SerializerMethodField()

    def get_actions(self, obj):
        return actions_for(self, "measurementpoint", obj.building_id)

    class Meta:
        model = MeasurementPoint
        fields = (
            "id",
            "code",
            "name",
            "point_type",
            "resource_type",
            "building",
            "laboratories",
            "meters_count",
            "actions",
        )


class MeasurementPointDataTableSerializer(DataTableSerializer):
    data = serializers.ListField(child=MeasurementPointSerializer(), required=True)


class MeasurementPointSaveSerializer(OrganizationScopedSerializer):
    building = serializers.PrimaryKeyRelatedField(queryset=Buildings.objects.none())
    laboratories = serializers.PrimaryKeyRelatedField(
        queryset=Laboratory.objects.none(), many=True, required=False
    )

    def scope_fields(self, fields, organization):
        fields["building"].queryset = self.visible_buildings(organization, "ambiental.view_measurementpoint")
        fields["laboratories"].child_relation.queryset = Laboratory.objects.filter(
            pk__in=organization.get_my_laboratories
        )

    def get_fields(self):
        fields = super().get_fields()
        fields["point_type"].queryset = Catalog.objects.filter(key=KEY_POINT_TYPE)
        fields["resource_type"].queryset = Catalog.objects.filter(key=KEY_RESOURCE_TYPE)
        return fields

    def validate(self, attrs):
        # El unique_together incluye la organización, que no viaja en el
        # formulario: sin esta validación el duplicado revienta como IntegrityError.
        code = attrs.get("code", getattr(self.instance, "code", None))
        resource_type = attrs.get(
            "resource_type", getattr(self.instance, "resource_type", None)
        )
        duplicated = MeasurementPoint.objects_with_deleted.filter(
            organization=self.get_organization(),
            code=code,
            resource_type=resource_type,
        )
        if self.instance is not None:
            duplicated = duplicated.exclude(pk=self.instance.pk)
        found = duplicated.first()
        if found is not None:
            message = _("There is already a measurement point with this code for this resource.")
            if found.is_deleted:
                message = _(
                    "There is already a measurement point with this code for this resource "
                    "in the trash; restore it instead of creating a new one."
                )
            raise serializers.ValidationError({"code": [message]})
        return attrs

    class Meta:
        model = MeasurementPoint
        fields = (
            "code",
            "name",
            "point_type",
            "resource_type",
            "building",
            "laboratories",
            "meters_count",
        )


# ---------------------------------------------------------------------------
# Registros de consumo
# ---------------------------------------------------------------------------


def resource_info_payload(point):
    """Lo que el formulario necesita saber del recurso de un punto."""
    info = get_resource_info(point.resource_type)
    unit = None
    if info["unit"]:
        unit = Catalog.objects.filter(key=KEY_MEASURE_UNIT, description=info["unit"]).first()
    return {
        "resource": point.resource_type.description,
        "unit": {"id": unit.pk, "text": unit.description} if unit else None,
        "is_waste": info["is_waste"],
        "extra_fields": list(info["extra_fields"]),
    }


class ConsumptionRecordSerializer(serializers.ModelSerializer):
    point = GTS2SerializerBase()
    building = serializers.SerializerMethodField()
    resource_type = serializers.SerializerMethodField()
    unit = GTS2SerializerBase()
    treatment = GTS2SerializerBase()
    waste_manager = GTS2SerializerBase()
    document = ChunkedFileField(required=False)
    resource_info = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    def get_fields(self):
        fields = super().get_fields()
        fields["period_start"] = date_field()
        fields["period_end"] = date_field()
        return fields

    def get_building(self, obj):
        building = obj.point.building
        return {"id": building.pk, "text": building.name} if building else None

    def get_resource_type(self, obj):
        resource = obj.point.resource_type
        return {"id": resource.pk, "text": resource.description}

    def get_resource_info(self, obj):
        return resource_info_payload(obj.point)

    def get_actions(self, obj):
        return actions_for(self, "consumptionrecord", obj.point.building_id)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Los campos extra viajan planos para que el formulario los rellene solo.
        for name in EXTRA_FIELDS:
            data[name] = (instance.extra_data or {}).get(name, "")
        return data

    class Meta:
        model = ConsumptionRecord
        fields = (
            "id",
            "point",
            "building",
            "resource_type",
            "period_start",
            "period_end",
            "quantity",
            "unit",
            "unit_cost",
            "total_cost",
            "is_waste",
            "treatment",
            "waste_manager",
            "document",
            "extra_data",
            "source",
            "note",
            "resource_info",
            "actions",
        )


class ConsumptionRecordDataTableSerializer(DataTableSerializer):
    data = serializers.ListField(child=ConsumptionRecordSerializer(), required=True)


class ConsumptionRecordSaveSerializer(OrganizationScopedSerializer):
    point = serializers.PrimaryKeyRelatedField(queryset=MeasurementPoint.objects.none())
    unit = serializers.PrimaryKeyRelatedField(
        queryset=Catalog.objects.filter(key=KEY_MEASURE_UNIT), required=False, allow_null=True
    )
    treatment = serializers.PrimaryKeyRelatedField(
        queryset=Catalog.objects.filter(key=KEY_WASTE_TREATMENT), required=False, allow_null=True
    )
    waste_manager = serializers.PrimaryKeyRelatedField(
        queryset=Provider.objects.none(), required=False, allow_null=True
    )
    document = ChunkedFileField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True)

    def get_fields(self):
        fields = super().get_fields()
        fields["period_start"] = date_field(allow_empty_str=False)
        fields["period_end"] = date_field(allow_empty_str=False)
        for name in EXTRA_FIELDS:
            fields[name] = serializers.CharField(
                required=False, allow_blank=True, write_only=True, max_length=150
            )
        return fields

    def scope_fields(self, fields, organization):
        fields["point"].queryset = MeasurementPoint.objects.filter(
            organization=organization,
            building__in=self.visible_buildings(organization, "ambiental.view_consumptionrecord"),
        )
        fields["waste_manager"].queryset = Provider.objects.filter(
            Q(laboratory__in=organization.get_my_laboratories) | Q(laboratory__isnull=True)
        )

    def validate(self, attrs):
        point = attrs.get("point", getattr(self.instance, "point", None))
        start = attrs.get("period_start", getattr(self.instance, "period_start", None))
        end = attrs.get("period_end", getattr(self.instance, "period_end", None))
        if start and end and end < start:
            raise serializers.ValidationError(
                {"period_end": [_("The period end must be after the period start.")]}
            )

        info = get_resource_info(point.resource_type)
        extra = {}
        for name in EXTRA_FIELDS:
            value = attrs.pop(name, "")
            if value and name in info["extra_fields"]:
                extra[name] = value.strip()
        attrs["extra_data"] = extra

        if not attrs.get("unit"):
            unit = None
            if info["unit"]:
                unit = Catalog.objects.filter(key=KEY_MEASURE_UNIT, description=info["unit"]).first()
            if unit is None:
                raise serializers.ValidationError({"unit": [_("This field is required.")]})
            attrs["unit"] = unit

        if not info["is_waste"]:
            attrs["treatment"] = None
            attrs["waste_manager"] = None
        if attrs.get("document") is False:
            attrs["document"] = None
        has_document = attrs.get("document") or (
            "document" not in attrs and self.instance is not None and self.instance.document
        )
        if not has_document and get_parameter(self.get_organization(), "ambiental.require_document"):
            raise serializers.ValidationError(
                {"document": [_("This organization requires the bill, receipt or manifest.")]}
            )

        overlapping = ConsumptionRecord.objects_with_deleted.filter(
            point=point, period_start__lte=end, period_end__gte=start
        )
        if self.instance is not None:
            overlapping = overlapping.exclude(pk=self.instance.pk)
        found = overlapping.order_by("period_start").first()
        if found is not None:
            message = _(
                "This measurement point already has a record from %(start)s to %(end)s "
                "that overlaps this period; edit that record instead."
            )
            if found.is_deleted:
                message = _(
                    "This measurement point has a record in the trash from %(start)s to "
                    "%(end)s that overlaps this period; restore it instead."
                )
            raise serializers.ValidationError(
                {"period_start": [message % {"start": found.period_start, "end": found.period_end}]}
            )
        return attrs

    class Meta:
        model = ConsumptionRecord
        fields = (
            "point",
            "period_start",
            "period_end",
            "quantity",
            "unit",
            "unit_cost",
            "total_cost",
            "treatment",
            "waste_manager",
            "document",
            "note",
        )


# ---------------------------------------------------------------------------
# Bases de normalización
# ---------------------------------------------------------------------------


class NormalizationBaseSerializer(serializers.ModelSerializer):
    normalizer = GTS2SerializerBase()
    building = GTS2SerializerBase()
    origin = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    def get_origin(self, obj):
        return _("Manual") if obj.is_manual else _("Preloaded")

    def get_actions(self, obj):
        return actions_for(self, "normalizationbase", obj.building_id)

    class Meta:
        model = NormalizationBase
        fields = ("id", "normalizer", "building", "year", "value", "is_manual", "origin", "actions")


class NormalizationBaseDataTableSerializer(DataTableSerializer):
    data = serializers.ListField(child=NormalizationBaseSerializer(), required=True)


class NormalizationBaseSaveSerializer(OrganizationScopedSerializer):
    normalizer = serializers.PrimaryKeyRelatedField(
        queryset=Catalog.objects.filter(key=KEY_NORMALIZER)
    )
    building = serializers.PrimaryKeyRelatedField(queryset=Buildings.objects.none())
    year = serializers.IntegerField(min_value=1900, max_value=2200)
    value = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)

    def scope_fields(self, fields, organization):
        fields["building"].queryset = self.visible_buildings(organization, "ambiental.view_normalizationbase")

    def validate(self, attrs):
        lookup = {
            name: attrs.get(name, getattr(self.instance, name, None))
            for name in ("normalizer", "building", "year")
        }
        duplicated = NormalizationBase.objects.filter(organization=self.get_organization(), **lookup)
        if self.instance is not None:
            duplicated = duplicated.exclude(pk=self.instance.pk)
        if duplicated.exists():
            raise serializers.ValidationError(
                {"year": [_("This building already has this base for that year; edit it instead.")]}
            )
        # Lo que escribe una persona manda sobre lo deducido: la precarga no lo pisa.
        attrs["is_manual"] = True
        return attrs

    class Meta:
        model = NormalizationBase
        fields = ("normalizer", "building", "year", "value")


class PreloadSerializer(serializers.Serializer):
    year = serializers.IntegerField(min_value=1900, max_value=2200)


# ---------------------------------------------------------------------------
# Alertas de consumo
# ---------------------------------------------------------------------------


class ConsumptionAlertSerializer(serializers.ModelSerializer):
    point = GTS2SerializerBase()
    building = serializers.SerializerMethodField()
    rule = GTS2SerializerBase()
    period = serializers.DateField(format="%m/%Y")
    reviewed_by = serializers.StringRelatedField()
    reviewed_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    actions = serializers.SerializerMethodField()

    def get_building(self, obj):
        building = obj.point.building
        return {"id": building.pk, "text": building.name} if building else None

    def get_actions(self, obj):
        if obj.reviewed:
            return {"review": False}
        return actions_for(
            self, "consumptionalert", obj.point.building_id,
            extra_perms={"review": "ambiental.review_consumptionalert"},
        )

    class Meta:
        model = ConsumptionAlert
        fields = (
            "id", "point", "building", "rule", "period", "reference_value", "registered_value",
            "variation_pct", "level", "message", "reviewed", "reviewed_note", "reviewed_by",
            "reviewed_at", "actions",
        )


class ConsumptionAlertDataTableSerializer(DataTableSerializer):
    data = serializers.ListField(child=ConsumptionAlertSerializer(), required=True)


class ReviewSerializer(serializers.Serializer):
    note = serializers.CharField(allow_blank=False, max_length=2000)
