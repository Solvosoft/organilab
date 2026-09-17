from django.utils.translation import gettext_lazy as _
from django_filters import FilterSet
from djgentelella.async_notification.registry import get_all_contexts
from djgentelella.serializers.selects import GTS2SerializerBase
from rest_framework import serializers

from auth_and_perms.models import Rol
from laboratory.models import Catalog
from presentation.alerts import (
    ALERT_PROCESSES,
    KEY_ALERT_TRIGGER,
    THRESHOLD_FIELDS,
    processes_for,
    validate_threshold,
)
from presentation.api_mixins import OrganizationLogsViewSet
from presentation.models import AlertEvent, AlertRule
from presentation.platform.base import OrganizationPermissionMixin

THRESHOLD_INPUTS = {field: trigger for trigger, (field, _label, _convert) in THRESHOLD_FIELDS.items()}


class DataTableSerializer(serializers.Serializer):
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class AlertRuleSerializer(serializers.ModelSerializer):
    process = serializers.SerializerMethodField()
    trigger = GTS2SerializerBase()
    level = serializers.SerializerMethodField()
    notify_roles = GTS2SerializerBase(many=True)
    threshold_display = serializers.SerializerMethodField()
    notification_code = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    def get_process(self, obj):
        info = ALERT_PROCESSES.get(obj.process)
        return {"id": obj.process, "text": str(info["label"]) if info else obj.process}

    def get_level(self, obj):
        return {"id": obj.level, "text": str(obj.get_level_display())}

    def get_notification_code(self, obj):
        return {"id": obj.notification_code, "text": obj.notification_code} if obj.notification_code else None

    def get_threshold_display(self, obj):
        field, label, _convert = THRESHOLD_FIELDS.get(obj.trigger.description, (None, "", None))
        return "%s: %s" % (label, obj.threshold.get(field, "")) if field else ""

    def get_actions(self, obj):
        user = self.context["request"].user
        return {
            "update": user.has_perm("presentation.change_alertrule"),
            "destroy": user.has_perm("presentation.delete_alertrule"),
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        field = THRESHOLD_FIELDS.get(instance.trigger.description, (None,))[0]
        for name in THRESHOLD_INPUTS:
            data[name] = instance.threshold.get(name, "") if name == field else ""
        return data

    class Meta:
        model = AlertRule
        fields = (
            "id", "name", "process", "trigger", "threshold_display", "level",
            "notification_code", "notify_roles", "notify_responsible", "create_task",
            "is_active", "actions",
        )


class AlertRuleDataTableSerializer(DataTableSerializer):
    data = serializers.ListField(child=AlertRuleSerializer(), required=True)


class AlertRuleSaveSerializer(serializers.ModelSerializer):
    trigger = serializers.PrimaryKeyRelatedField(queryset=Catalog.objects.filter(key=KEY_ALERT_TRIGGER))
    notify_roles = serializers.PrimaryKeyRelatedField(queryset=Rol.objects.all(), many=True, required=False)
    notification_code = serializers.CharField(required=False, allow_blank=True, default="")

    def get_fields(self):
        fields = super().get_fields()
        user = self.context["request"].user
        fields["process"] = serializers.ChoiceField(
            choices=[(code, info["label"]) for code, info in processes_for(user).items()]
        )
        for name in THRESHOLD_INPUTS:
            fields[name] = serializers.CharField(required=False, allow_blank=True, write_only=True)
        return fields

    def validate_notification_code(self, value):
        if value and value not in get_all_contexts():
            raise serializers.ValidationError(_("Unknown email process."))
        return value

    def validate(self, attrs):
        trigger = attrs["trigger"]
        process = ALERT_PROCESSES[attrs["process"]]
        if trigger.description not in process["triggers"]:
            raise serializers.ValidationError({"trigger": [_("This trigger does not apply to the process.")]})
        field = THRESHOLD_FIELDS[trigger.description][0]
        raw = attrs.get(field, "")
        for name in THRESHOLD_INPUTS:
            attrs.pop(name, None)
        try:
            attrs["threshold"] = validate_threshold(trigger.description, raw)
        except ValueError as error:
            raise serializers.ValidationError({field: [str(error)]})
        return attrs

    class Meta:
        model = AlertRule
        fields = (
            "name", "process", "trigger", "level", "notification_code", "notify_roles",
            "notify_responsible", "create_task", "is_active",
        )


class AlertRuleFilter(FilterSet):
    class Meta:
        model = AlertRule
        fields = {"name": ["icontains"], "process": ["exact"], "trigger": ["exact"], "is_active": ["exact"]}


class AlertRuleViewSet(OrganizationPermissionMixin, OrganizationLogsViewSet):
    serializer_class = {
        "list": AlertRuleDataTableSerializer,
        "create": AlertRuleSaveSerializer,
        "update": AlertRuleSaveSerializer,
        "retrieve": AlertRuleSerializer,
        "get_values_for_update": AlertRuleSerializer,
    }
    perms = {
        "list": ["presentation.view_alertrule"],
        "create": ["presentation.add_alertrule"],
        "update": ["presentation.change_alertrule"],
        "retrieve": ["presentation.view_alertrule"],
        "get_values_for_update": ["presentation.change_alertrule"],
        "destroy": ["presentation.delete_alertrule"],
    }
    queryset = AlertRule.objects.select_related("trigger").prefetch_related("notify_roles")
    search_fields = ["name", "process"]
    filterset_class = AlertRuleFilter
    ordering_fields = ["name", "process"]
    ordering = ("process", "name")

    def get_queryset(self):
        return super().get_queryset().filter(process__in=list(processes_for(self.request.user)))


class AlertEventSerializer(serializers.ModelSerializer):
    rule = GTS2SerializerBase()
    level = serializers.CharField(source="get_level_display")
    creation_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = AlertEvent
        fields = ("id", "rule", "message", "level", "link", "recipients", "creation_date")


class AlertEventDataTableSerializer(DataTableSerializer):
    data = serializers.ListField(child=AlertEventSerializer(), required=True)


class AlertEventFilter(FilterSet):
    class Meta:
        model = AlertEvent
        fields = {"rule": ["exact"], "level": ["exact"], "message": ["icontains"]}


class AlertEventViewSet(OrganizationPermissionMixin, OrganizationLogsViewSet):
    serializer_class = {"list": AlertEventDataTableSerializer}
    perms = {"list": ["presentation.view_alertrule"]}
    http_method_names = ["get"]
    queryset = AlertEvent.objects.select_related("rule")
    search_fields = ["message", "rule__name"]
    filterset_class = AlertEventFilter
    ordering_fields = ["creation_date"]
    ordering = ("-creation_date",)

    def get_queryset(self):
        return super().get_queryset().filter(rule__process__in=list(processes_for(self.request.user)))
