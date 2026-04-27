import logging

from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from djgentelella.serializers import GTDateTimeField
from djgentelella.serializers.selects import GTS2SerializerBase
from rest_framework import serializers

from auth_and_perms.models import Profile, Rol
from pending_tasks.models import PendingTask

logger = logging.getLogger("organilab")


class PendingTaskSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    creation_date = GTDateTimeField()
    profile = GTS2SerializerBase()
    rols = GTS2SerializerBase(many=True)

    def get_status(self, obj):
        return {"id": obj.status, "name": obj.get_status_display()}

    class Meta:
        model = PendingTask
        fields = [
            "id",
            "name",
            "description",
            "creation_date",
            "status",
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
