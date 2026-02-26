from django.conf import settings
from django.utils.translation import gettext_lazy as _
from djgentelella.serializers.selects import GTS2SerializerBase
from rest_framework import serializers

from auth_and_perms.api.serializers import ValidateUserAccessOrgLabSerializer
from laboratory.models import (
    LaboratoryRoom,
    Laboratory,
    Object,
    Catalog,
    PrecursorReportValues,
    PrecursorReport,
)
from laboratory.utils import get_actions_by_perms
from report.models import ObjectChangeLogReportBuilder, RegencyReportBuilder


class ReportDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(
        child=serializers.ListSerializer(child=serializers.CharField()), required=True
    )
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class ValidateUserAccessLabRoomSerializer(ValidateUserAccessOrgLabSerializer):
    lab_room = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=LaboratoryRoom.objects.using(settings.READONLY_DATABASE),
        allow_null=True,
        required=False,
    )
    all_labs_org = serializers.BooleanField(default=False)


class ObjectChangeLogSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    update_time = serializers.SerializerMethodField()

    def get_user(self, obj):
        if not obj:
            return _("No user found")

        if not obj.user:
            return _("No user found")

        name = obj.user.get_full_name()
        if not name:
            name = obj.user.username
        return name

    def get_update_time(self, obj):
        if obj.update_time:
            return obj.update_time.strftime("%m/%d/%Y, %H:%M:%S")
        return ""

    class Meta:
        model = ObjectChangeLogReportBuilder
        fields = "__all__"


class ObjectChangeDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ObjectChangeLogSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class ValidateObjectChangeFilters(serializers.Serializer):
    laboratory = serializers.PrimaryKeyRelatedField(
        queryset=Laboratory.objects.all().using(settings.READONLY_DATABASE)
    )
    object = serializers.PrimaryKeyRelatedField(
        queryset=Object.objects.all().using(settings.READONLY_DATABASE)
    )
    unit = serializers.PrimaryKeyRelatedField(
        queryset=Catalog.objects.filter(key="units").using(settings.READONLY_DATABASE)
    )


class RegencySerializer(serializers.ModelSerializer):
    substance = GTS2SerializerBase(required=False)
    danger_category = serializers.CharField(required=False)
    total = serializers.FloatField(required=False)
    break_threshold = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    def get_break_threshold(self, obj):
        if obj.break_threshold:
            return _("Yes")
        return _("No")

    def get_actions(self, obj):
        user = self.context["request"].user
        action_list = {
            "create": False,
            "update": False,
            "destroy": False,
            "detail": False,
            "list": user.has_perm("laboratory.do_report"),
        }
        return action_list

    class Meta:
        model = RegencyReportBuilder
        fields = [
            "id",
            "substance",
            "total",
            "break_threshold",
            "danger_category",
            "actions",
        ]


class RegencyDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=RegencySerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


# PrecursorReportValues
class PrecursorReportValuesSerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    object = GTS2SerializerBase(many=False)
    precursor_report = GTS2SerializerBase(many=False)
    measurement_unit = GTS2SerializerBase(many=False)

    def get_actions(self, obj):
        user = self.context["request"].user
        return {
            "create": user.has_perm("laboratory.add_precursorreportvalues"),
            "update": user.has_perm("laboratory.change_precursorreportvalues"),
            "destroy": user.has_perm("laboratory.delete_precursorreportvalues"),
            "list": user.has_perm("laboratory.view_precursorreportvalues"),
        }

    class Meta:
        model = PrecursorReportValues
        fields = "__all__"


class PrecursorReportValuesDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=PrecursorReportValuesSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class PrecursorReportValuesValidateSerializer(serializers.ModelSerializer):
    precursor_report = serializers.PrimaryKeyRelatedField(
        queryset=PrecursorReport.objects.all(), required=False
    )
    object = serializers.PrimaryKeyRelatedField(
        queryset=Object.objects.filter(
            type=0, sustancecharacteristics__is_precursor=True
        ),
        required=True,
    )
    measurement_unit = serializers.PrimaryKeyRelatedField(
        queryset=Catalog.objects.filter(key="units"), required=True
    )
    quantity = serializers.FloatField(required=True)
    previous_balance = serializers.FloatField(required=True)
    new_income = serializers.FloatField(required=True)
    bills = serializers.CharField(required=False, allow_blank=True, max_length=200)
    providers = serializers.CharField(required=False, allow_blank=True, max_length=200)
    stock = serializers.FloatField(required=True)
    month_expense = serializers.FloatField(required=True)
    final_balance = serializers.FloatField(required=True)
    reason_to_spend = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = PrecursorReportValues
        fields = (
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
        )
