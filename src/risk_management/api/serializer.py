from django.contrib.auth.models import User
from djgentelella.fields.files import ChunkedFileField
from djgentelella.serializers import GTDateField, GTDateTimeField
from djgentelella.serializers.selects import GTS2SerializerBase
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from laboratory.models import Laboratory
from laboratory.utils import get_users_from_organization
from risk_management.models import Regent, Buildings, Structure, RiskZone, \
    IncidentReport


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

class IncidentReportSerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    laboratories = GTS2SerializerBase(many=True)
    buildings = GTS2SerializerBase(many=True)
    incident_date = GTDateField()
    creation_date = GTDateTimeField()
    risk_zone = GTS2SerializerBase(many=False)

    def get_actions(self, obj):
        user = self.context["request"].user
        perms = {
            "list":False,
            "create":False,
            "update":False,
            "destroy":False,
            "download_pdf":False
        }
        if user.has_perm('risk_management.view_incidentreport'):
            perms["list"] = True

        if user.has_perm('risk_management.add_incidentreport'):
            perms["create"] = True
        if user.has_perm('risk_management.change_incidentreport'):
            perms["update"] = True
        if user.has_perm('risk_management.delete_incidentreport'):
            perms["destroy"] = True
        if user.has_perm('laboratory.do_report'):
            perms["download_pdf"] = True

        return perms


    class Meta:
        model = IncidentReport
        fields = "__all__"


class IncidentReportDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=IncidentReportSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class ActionIncidentReportSerializer(serializers.ModelSerializer):

    buildings = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=Buildings.objects.all(),
        allow_null=False,
        allow_empty=False,
    )
    laboratories = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=Laboratory.objects.all(),
        allow_null=False,
        allow_empty=False,
    )
    short_description = serializers.CharField(max_length=500, required=True)
    incident_date = GTDateField(allow_null=True, required=False)
    causes = serializers.CharField(required=True)
    environment_impact = serializers.CharField(required=True)
    result_of_plans = serializers.CharField(required=True)
    mitigation_actions = serializers.CharField(required=True)
    recomendations = serializers.CharField(required=True)
    notification_copy = ChunkedFileField(allow_null=True, required=False,
                                  allow_empty_file=True)


    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        organization = self.context.get("org_pk", None)
        risk = self.context.get("risk_pk", None)
        if risk:
            risk = get_object_or_404(RiskZone, pk=risk)
            fields['buildings'].queryset = (Buildings.objects.
                                            filter(pk__in=risk.buildings.
                                                   values_list("pk", flat=True)))
        fields['laboratories'].queryset = Laboratory.objects.filter(pk__in=get_users_from_organization(organization))

        return fields

    class Meta:
        model = IncidentReport
        fields = (
            "buildings",
            "laboratories",
            "short_description",
            "causes",
            "infraestructure_impact",
            "people_impact",
            "environment_impact",
            "result_of_plans",
            "mitigation_actions",
            "recomendations",
            "notification_copy",
            'incident_date'
        )
