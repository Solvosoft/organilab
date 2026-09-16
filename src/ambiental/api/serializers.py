from django.utils.translation import gettext_lazy as _
from djgentelella.serializers.selects import GTS2SerializerBase
from rest_framework import serializers

from ambiental.ambiental_defaults import KEY_POINT_TYPE, KEY_RESOURCE_TYPE
from ambiental.models import MeasurementPoint
from laboratory.models import Catalog, Laboratory
from risk_management.models import Buildings


def actions_for(user, model_name, extra=None):
    """Acciones de fila que el datatable de ObjectCRUD muestra u oculta."""
    actions = {
        "update": user.has_perm("ambiental.change_%s" % model_name),
        "destroy": user.has_perm("ambiental.delete_%s" % model_name),
    }
    actions.update(extra or {})
    return actions


class DataTableSerializer(serializers.Serializer):
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class OrganizationScopedSerializer(serializers.ModelSerializer):
    """Acota los querysets de las relaciones a la organización de la URL."""

    def get_organization(self):
        return self.context.get("organization")

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
        return actions_for(self.context["request"].user, "measurementpoint")

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
        fields["building"].queryset = Buildings.objects.filter(organization=organization)
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
