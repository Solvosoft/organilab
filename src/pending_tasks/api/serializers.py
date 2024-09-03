from rest_framework import serializers

from auth_and_perms.models import Profile, Rol
from pending_tasks.models import PendingTask
from djgentelella.widgets import core as genwidgets


class PendingTaskSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    validate_profile = serializers.SerializerMethodField()
    rols = serializers.SerializerMethodField()

    def get_status(self, obj):
        return {'id': obj.status, 'name': self.get_status_display(obj)}

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_validate_profile(self, obj):
        if obj.validate_profile:
            return {'id': obj.validate_profile.id, 'name': obj.validate_profile.user.username}

    def get_rols(self, obj):
        return [{'id': rol.id, 'name': rol.name} for rol in obj.rols.all()]

    class Meta:
        model = PendingTask
        fields = ['id', 'creation_date', 'description', 'status', 'status_display', 'link', 'validate_profile', 'rols']

class PendingTaskValidateSerializer(serializers.ModelSerializer):
    description = serializers.CharField(required=False)
    # status = serializers.IntegerField(min_value=0, max_value=2, default=0)
    validate_profile = serializers.PrimaryKeyRelatedField(queryset=Profile.objects.all(), required=False, allow_null=True, allow_empty=True)
    rols = serializers.PrimaryKeyRelatedField(queryset=Rol.objects.all(), many=True)
    link = serializers.URLField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = PendingTask
        fields = '__all__'

class PendingTaskListSerializer(serializers.Serializer):
    data = serializers.ListField(child=PendingTaskSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)
