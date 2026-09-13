"""Serializers de la capa labview.

La diferencia con los actuales es una: **las acciones viajan como datos**.
``ShelfObjectLaboratoryViewSerializer`` devuelve el campo ``actions`` como una
cadena de HTML de 124 líneas renderizada una vez por fila; aquí es un
diccionario ``{accion: bool}``, el mismo patrón que ya usa
``risk_management/api/serializer.py``.
"""

from rest_framework import serializers

from laboratory.api.labview.actions import (
    get_shelfobject_action_variants,
    get_shelfobject_actions,
)
from laboratory.api.serializers import ShelfObjectLaboratoryViewSerializer
from laboratory.models import (
    Furniture,
    LaboratoryRoom,
    Object,
    Shelf,
    ShelfObject,
)


class LabRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = LaboratoryRoom
        fields = ["id", "name"]


class ValidateLabRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = LaboratoryRoom
        fields = ["name"]


class FurnitureSerializer(serializers.ModelSerializer):
    type_name = serializers.SerializerMethodField()

    def get_type_name(self, obj):
        return str(obj.type) if obj.type else ""

    class Meta:
        model = Furniture
        fields = ["id", "name", "type", "type_name", "color", "labroom"]


class ValidateFurnitureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Furniture
        fields = ["name", "type", "color"]


class ShelfSerializer(serializers.ModelSerializer):
    type_name = serializers.SerializerMethodField()
    measurement_unit_name = serializers.SerializerMethodField()

    def get_type_name(self, obj):
        return str(obj.type) if obj.type else ""

    def get_measurement_unit_name(self, obj):
        return obj.get_measurement_unit_display()

    class Meta:
        model = Shelf
        fields = [
            "id",
            "name",
            "type",
            "type_name",
            "color",
            "discard",
            "quantity",
            "measurement_unit",
            "measurement_unit_name",
            "infinity_quantity",
            "description",
            "limit_only_objects",
            "furniture",
        ]


class ValidateShelfSerializer(serializers.ModelSerializer):
    """Las reglas de ``ShelfForm.clean`` (``views/shelfs.py:134``), tal cual."""

    row = serializers.IntegerField(min_value=0, write_only=True)
    col = serializers.IntegerField(min_value=0, write_only=True)
    available_objects_when_limit = serializers.PrimaryKeyRelatedField(
        queryset=Object.objects.all(), many=True, required=False
    )

    class Meta:
        model = Shelf
        fields = [
            "name",
            "type",
            "color",
            "discard",
            "infinity_quantity",
            "quantity",
            "measurement_unit",
            "description",
            "limit_only_objects",
            "available_objects_when_limit",
            "row",
            "col",
        ]

    def validate(self, data):
        data = super().validate(data)
        quantity = data.get("quantity", 0)
        unit = data.get("measurement_unit")
        infinity = data.get("infinity_quantity", False)

        if unit is None and quantity <= 0 and not infinity:
            raise serializers.ValidationError(
                {
                    "quantity": (
                        "The quantity need to be greater than 0, when dont select "
                        "an unit and check the field infinity quantity."
                    ),
                    "measurement_unit": (
                        "Need a unit when the dont check the field infinity quantity."
                    ),
                }
            )
        if unit is not None and quantity <= 0 and not infinity:
            raise serializers.ValidationError(
                {"quantity": "The quantity need to be greater than 0"}
            )
        if quantity < 0:
            raise serializers.ValidationError(
                {"quantity": "The quantity need to be greater than 0"}
            )
        if unit is None and data.get("discard") and not infinity:
            raise serializers.ValidationError(
                {
                    "measurement_unit": (
                        "When a shelf if discard you need to add a measurement unit"
                    )
                }
            )
        return data


class ShelfMoveSerializer(serializers.Serializer):
    row = serializers.IntegerField(min_value=0)
    col = serializers.IntegerField(min_value=0)


class GridIndexSerializer(serializers.Serializer):
    index = serializers.IntegerField(min_value=0, required=False, allow_null=True)


class ShelfAvailabilitySerializer(serializers.ModelSerializer):
    """El JSON que sustituye al HTML de ``shelf_availability_information``."""

    type_name = serializers.SerializerMethodField()
    measurement_unit_name = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    occupancy_percent = serializers.SerializerMethodField()

    def get_type_name(self, obj):
        return str(obj.type) if obj.type else ""

    def get_measurement_unit_name(self, obj):
        return obj.get_measurement_unit_display()

    def get_total(self, obj):
        if not obj.measurement_unit:
            return None
        return round(
            obj.get_total_refuse(
                include_containers=False, measurement_unit=obj.measurement_unit
            ),
            3,
        )

    def get_occupancy_percent(self, obj):
        # Sin unidad o con capacidad infinita el porcentaje no significa nada,
        # y la plantilla actual pinta "-------" en ese caso.
        if obj.infinity_quantity or not obj.measurement_unit:
            return None
        return round(
            obj.get_refuse_porcentage(
                include_containers=False, measurement_unit=obj.measurement_unit
            ),
            2,
        )

    class Meta:
        model = Shelf
        fields = [
            "id",
            "name",
            "type_name",
            "discard",
            "quantity",
            "infinity_quantity",
            "measurement_unit_name",
            "total",
            "occupancy_percent",
            "limit_only_objects",
        ]


class LabviewShelfObjectSerializer(ShelfObjectLaboratoryViewSerializer):
    """La fila de la tabla, con ``actions`` como diccionario.

    Hereda del serializer de la vista antigua a propósito: así los textos de
    tipo, nombre, cantidad y unidad —que están traducidos— salen del mismo
    sitio y no pueden divergir.  Lo único que se reescribe es ``actions``, que
    deja de ser HTML renderizado por fila y pasa a ser datos.
    """

    actions = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    object_raw_name = serializers.SerializerMethodField()
    container_id = serializers.SerializerMethodField()
    container_display = serializers.SerializerMethodField()

    def get_type(self, obj):
        return obj.object.type

    def get_object_raw_name(self, obj):
        # ``object_name`` lleva la cantidad cuando es una caja; el borrado
        # necesita el nombre a secas para preguntar "¿seguro?".
        return obj.object.name

    def get_container_id(self, obj):
        return obj.container_id

    def get_container_display(self, obj):
        # El select2 de "gestionar contenedor" muestra el ``__str__`` completo
        # (nombre, cantidad y unidad), no solo el nombre del objeto.
        return str(obj.container) if obj.container else ""

    def get_actions(self, obj):
        return get_shelfobject_actions(self.context["request"].user, obj)

    def get_variants(self, obj):
        return get_shelfobject_action_variants(obj)

    class Meta(ShelfObjectLaboratoryViewSerializer.Meta):
        fields = ShelfObjectLaboratoryViewSerializer.Meta.fields + [
            "type",
            "is_box",
            "shelf",
            "object_raw_name",
            "container_id",
            "container_display",
            "reactive_expiration_date",
            "quantity_units",
            "variants",
        ]


class LabviewShelfObjectTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=LabviewShelfObjectSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)
