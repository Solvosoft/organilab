from djgentelella.serializers import GTDateField
from rest_framework import serializers

from laboratory.models import SDSTraceability


class SDSTraceabilitySerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    sustance_characteristics_name = serializers.SerializerMethodField()
    sustance_characteristics_cas_id_number = serializers.SerializerMethodField()
    verified_by_name = serializers.SerializerMethodField()
    security_sheet_url = serializers.SerializerMethodField()
    verified_date = GTDateField()

    def get_actions(self, obj):
        user = self.context["request"].user
        return {
            "list": user.has_perm("laboratory.view_sdstraceability"),
            "verify": user.has_perm("laboratory.change_sdstraceability"),
            "create": False,
            "update": False,
            "destroy": False,
            "verified": obj.is_verified,
        }

    def get_sustance_characteristics_name(self, obj):
        if obj.sustance_characteristics:
            return obj.sustance_characteristics.obj.name
        return ""

    def get_sustance_characteristics_cas_id_number(self, obj):
        if obj.sustance_characteristics:
            return obj.sustance_characteristics.cas_id_number
        return ""

    def get_verified_by_name(self, obj):
        if obj.verified_by:
            return obj.verified_by.get_full_name() or obj.verified_by.username
        return ""

    def get_security_sheet_url(self, obj):
        if obj.security_sheet:
            return obj.security_sheet.url
        return ""

    class Meta:
        model = SDSTraceability
        fields = [
            "id",
            "sustance_characteristics",
            "sustance_characteristics_name",
            "source",
            "verified_by",
            "verified_by_name",
            "is_verified",
            "security_sheet",
            "security_sheet_url",
            "sustance_characteristics_cas_id_number",
            "verified_date",
            "actions",
        ]


class SDSTraceabilityDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=SDSTraceabilitySerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class SDSTraceabilityValidateSerializer(serializers.ModelSerializer):
    is_verified = serializers.BooleanField(required=False)

    class Meta:
        model = SDSTraceability
        fields = [
            "is_verified",
        ]
