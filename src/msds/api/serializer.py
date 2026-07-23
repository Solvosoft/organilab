from djgentelella.serializers import GTDateField
from rest_framework import serializers

from laboratory.models import SDSTraceability, SustanceCharacteristics
from django.utils.translation import gettext_lazy as _


class SDSTraceabilitySerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    sustance_characteristics_name = serializers.SerializerMethodField()
    sustance_characteristics_cas_id_number = serializers.SerializerMethodField()
    verified_by_name = serializers.SerializerMethodField()
    security_sheet_url = serializers.SerializerMethodField()
    verified_date = GTDateField()
    hcodes = serializers.SerializerMethodField()

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
        if obj.sustance_characteristics.security_sheet:
            return obj.sustance_characteristics.security_sheet.url
        return ""

    def get_hcodes(self, obj):
        if obj.sustance_characteristics.h_code.all():
            codes = set(
                [hc.code.__str__() for hc in obj.sustance_characteristics.h_code.all()]
            )
            return ", ".join(codes) if len(codes) > 0 else ""
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
            "hcodes",
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


class SustanceCharacteristicsSerializer(serializers.ModelSerializer):
    obj_name = serializers.SerializerMethodField()
    iarc_name = serializers.SerializerMethodField()
    imdg_name = serializers.SerializerMethodField()
    precursor_type_name = serializers.SerializerMethodField()
    white_organ_list = serializers.SerializerMethodField()
    h_code_list = serializers.SerializerMethodField()
    ue_code_list = serializers.SerializerMethodField()
    nfpa_list = serializers.SerializerMethodField()
    storage_class_list = serializers.SerializerMethodField()
    security_sheet_url = serializers.SerializerMethodField()
    is_precursor = serializers.SerializerMethodField()
    molecular_formula = serializers.SerializerMethodField()
    cas_id_number = serializers.SerializerMethodField()

    def get_is_precursor(self, obj):
        if obj.is_precursor:
            return _("Yes")
        return _("No")

    def get_molecular_formula(self, obj):
        if obj.valid_molecular_formula:
            return obj.molecular_formula
        return ""

    def get_cas_id_number(self, obj):
        if obj.cas_id_number:
            return obj.cas_id_number
        return ""

    def get_obj_name(self, obj):
        return obj.obj.name if obj.obj else ""

    def get_iarc_name(self, obj):
        return str(obj.iarc) if obj.iarc else ""

    def get_imdg_name(self, obj):
        return str(obj.imdg) if obj.imdg else ""

    def get_precursor_type_name(self, obj):
        return str(obj.precursor_type) if obj.precursor_type else ""

    def get_white_organ_list(self, obj):
        return [str(wo) for wo in obj.white_organ.all()]

    def get_h_code_list(self, obj):
        return [hc.__str__() for hc in obj.h_code.all()]

    def get_ue_code_list(self, obj):
        return [str(ue) for ue in obj.ue_code.all()]

    def get_nfpa_list(self, obj):
        return [str(nfpa) for nfpa in obj.nfpa.all()]

    def get_storage_class_list(self, obj):
        return [str(sc) for sc in obj.storage_class.all()]

    def get_security_sheet_url(self, obj):
        if obj.security_sheet:
            return obj.security_sheet.url
        return ""

    class Meta:
        model = SustanceCharacteristics
        fields = [
            "id",
            "obj_name",
            "cas_id_number",
            "molecular_formula",
            "valid_molecular_formula",
            "is_precursor",
            "precursor_type",
            "precursor_type_name",
            "iarc",
            "iarc_name",
            "imdg",
            "imdg_name",
            "bioaccumulable",
            "seveso_list",
            "security_sheet_url",
            "white_organ_list",
            "h_code_list",
            "ue_code_list",
            "nfpa_list",
            "storage_class_list",
        ]
