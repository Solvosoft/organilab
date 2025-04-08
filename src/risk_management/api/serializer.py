from django.contrib.auth.models import User
from djgentelella.serializers.selects import GTS2SerializerBase
from rest_framework import serializers

from laboratory.utils import get_users_from_organization
from risk_management.models import Regent, Buildings, Structure


class AddRegentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        many=False,
        required=True,
        queryset=User.objects.none(),
        allow_null=False,
        allow_empty=False,
    )

    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        organization = self.context.get("org_pk", None)
        fields['user'].queryset = User.objects.filter(pk__in=get_users_from_organization(organization))


        return fields

    class Meta:
        model = Regent
        fields = (
            "user",
        )

class RegentSerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    user = GTS2SerializerBase(many=False)

    def get_actions(self, obj):
        user = self.context["request"].user


        return {
            "list": True,
            "create": True,
            "update": False,
            "destroy": True,
        }


    class Meta:
        model = Regent
        fields = "__all__"


class RegentDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=RegentSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class BuildingSerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    laboratories = GTS2SerializerBase(many=True)
    nearby_buildings = GTS2SerializerBase(many=True)
    regents = GTS2SerializerBase(many=True)
    manager = GTS2SerializerBase(many=False)
    geolocation = serializers.SerializerMethodField()

    def get_geolocation(self, obj):
        return obj.geolocation

    def get_actions(self, obj):
        user = self.context["request"].user


        return {
            "list": True,
            "create": False,
            "update": False,
            "destroy": True,
        }


    class Meta:
        model = Buildings
        fields = "__all__"


class BuildingDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=BuildingSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class StructureSerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    buildings = GTS2SerializerBase(many=True)
    manager = GTS2SerializerBase(many=False)
    type_structure = GTS2SerializerBase(many=False)
    geolocation = serializers.SerializerMethodField()

    def get_geolocation(self, obj):
        return obj.geolocation

    def get_actions(self, obj):
        user = self.context["request"].user


        return {
            "list": True,
            "create": False,
            "update": False,
            "destroy": True,
        }


    class Meta:
        model = Structure
        fields = "__all__"


class StructureDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=StructureSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)
