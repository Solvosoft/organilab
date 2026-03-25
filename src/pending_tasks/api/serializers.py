import logging
from django.utils.translation import gettext_lazy as _

from djgentelella.serializers import GTDateTimeField
from djgentelella.serializers.selects import GTS2SerializerBase
from rest_framework import serializers

from auth_and_perms.models import Profile, Rol
from organilab import settings
from pending_tasks.models import PendingTask

logger = logging.getLogger("organilab")


class PendingTaskSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    creation_date = GTDateTimeField()
    profile = GTS2SerializerBase()
    rols = GTS2SerializerBase(many=True)

    def get_status(self, obj):
        return {"id": obj.status, "name": self.get_status_display(obj)}

    def get_status_display(self, obj):
        return obj.get_status_display()

    class Meta:
        model = PendingTask
        fields = [
            "id",
            "name",
            "description",
            "creation_date",
            "status",
            "status_display",
            "link",
            "profile",
            "rols",
            "is_archived",
        ]


class PendingTaskValidateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    profile = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(),
        required=False,
        allow_null=True,
        allow_empty=True,
    )
    rols = serializers.PrimaryKeyRelatedField(queryset=Rol.objects.all(), many=True)
    link = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    is_archived = serializers.BooleanField(default=False)

    class Meta:
        model = PendingTask
        fields = [
            "id",
            "name",
            "description",
            "status",
            "profile",
            "rols",
            "link",
            "is_archived",
        ]


class PendingTaskListSerializer(serializers.Serializer):
    data = serializers.ListField(child=PendingTaskSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class ProfileValidateSerializer(serializers.Serializer):
    profile = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.using(settings.READONLY_DATABASE), required=True
    )

    def validate(self, data):
        task = self.context.get("task")
        if task.profile:
            logger.debug(
                f"ProfileValidateSerializer --> Task {task.id} already assigned to user {task.profile}"
            )
            raise serializers.ValidationError(
                {"task": _("Task already assigned to another user")}
            )
        return data


class SessionProfileValidateSerializer(serializers.Serializer):
    profile = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.using(settings.READONLY_DATABASE), required=True
    )

    def validate(self, data):
        task = self.context.get("task")
        profile = data["profile"]
        if task.profile != profile:
            logger.debug(
                f"SessionProfileValidateSerializer --> Task {task.id} not assigned to user {profile}"
            )
            raise serializers.ValidationError({"task": _("Task not assigned to user")})
        return data


class CurrentStatusValidateSerializer(SessionProfileValidateSerializer):
    profile = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.using(settings.READONLY_DATABASE), required=True
    )

    def validate(self, data):
        data = super().validate(data)
        task = self.context.get("task")
        if task.status != PendingTask.PENDING:
            logger.debug(
                f"CurrentStatusValidateSerializer --> Task {task.id} is not pending"
            )
            raise serializers.ValidationError({"task": _("Task is not pending")})
        return data


class PendingTaskGetValuesSerializer(serializers.ModelSerializer):
    profile = GTS2SerializerBase(allow_null=True)
    rols = GTS2SerializerBase(many=True)
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return {"id": obj.status, "text": obj.get_status_display()}

    class Meta:
        model = PendingTask
        fields = [
            "id",
            "name",
            "description",
            "status",
            "link",
            "profile",
            "rols",
            "is_archived",
        ]


class NewStatusValidateSerializer(SessionProfileValidateSerializer):
    profile = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.using(settings.READONLY_DATABASE), required=True
    )
    status = serializers.IntegerField(min_value=0, max_value=2)
