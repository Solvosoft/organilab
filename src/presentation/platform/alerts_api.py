from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from django_filters import FilterSet
from djgentelella.async_notification.registry import get_all_contexts
from djgentelella.serializers import DataTableSerializer
from djgentelella.serializers.selects import GTS2SerializerBase
from rest_framework import serializers

from auth_and_perms.models import Rol
from presentation.alerts import (
    get_process,
    get_trigger,
    processes_for,
    threshold_display,
    threshold_fields,
    trigger_choices,
    validate_threshold,
)
from presentation.api_mixins import OrganizationLogsViewSet
from presentation.models import AlertEvent, AlertRule
from presentation.platform.base import OrganizationPermissionMixin


def trigger_label(code):
    try:
        return str(get_trigger(code).label)
    except DjangoValidationError:
        return code


class AlertRuleSerializer(serializers.ModelSerializer):
    process = serializers.SerializerMethodField()
    trigger = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    notify_roles = GTS2SerializerBase(many=True)
    threshold_display = serializers.SerializerMethodField()
    notification_code = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    def get_process(self, obj):
        process = get_process(obj.process)
        return {"id": obj.process, "text": str(process.label) if process else obj.process}

    def get_trigger(self, obj):
        return {"id": obj.trigger, "text": trigger_label(obj.trigger)}

    def get_level(self, obj):
        return {"id": obj.level, "text": str(obj.get_level_display())}

    def get_notification_code(self, obj):
        return {"id": obj.notification_code, "text": obj.notification_code} if obj.notification_code else None

    def get_threshold_display(self, obj):
        return threshold_display(obj)

    def get_actions(self, obj):
        user = self.context["request"].user
        return {
            "update": user.has_perm("presentation.change_alertrule"),
            "destroy": user.has_perm("presentation.delete_alertrule"),
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for name in threshold_fields():
            data[name] = (instance.threshold or {}).get(name, "")
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
    trigger = serializers.ChoiceField(choices=())
    notify_roles = serializers.PrimaryKeyRelatedField(queryset=Rol.objects.all(), many=True, required=False)
    notification_code = serializers.CharField(required=False, allow_blank=True, default="")

    def get_fields(self):
        fields = super().get_fields()
        user = self.context["request"].user
        processes = processes_for(user)
        fields["process"] = serializers.ChoiceField(
            choices=[(code, process.label) for code, process in processes.items()]
        )
        fields["trigger"].choices = trigger_choices()
        for name in threshold_fields():
            fields[name] = serializers.CharField(required=False, allow_blank=True, write_only=True)
        return fields

    def validate_notification_code(self, value):
        if value and value not in get_all_contexts():
            raise serializers.ValidationError(_("Unknown email process."))
        return value

    def validate(self, attrs):
        trigger = attrs["trigger"]
        process = get_process(attrs["process"])
        if trigger not in process.triggers:
            raise serializers.ValidationError({"trigger": [_("This trigger does not apply to the process.")]})
        raw = {name: attrs.pop(name, "") for name in threshold_fields()}
        try:
            attrs["threshold"] = validate_threshold(trigger, raw)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                {name: [str(message) for message in messages] for name, messages in error.message_dict.items()}
            )
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
    queryset = AlertRule.objects.prefetch_related("notify_roles")
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
    resolved_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = AlertEvent
        fields = ("id", "rule", "message", "level", "link", "recipients", "creation_date", "resolved_at")


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
