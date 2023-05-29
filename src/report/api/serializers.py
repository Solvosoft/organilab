from rest_framework import serializers
from django.conf import settings
from auth_and_perms.api.serializers import ValidateUserAccessOrgLabSerializer
from laboratory.models import LaboratoryRoom


class ReportDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=serializers.ListSerializer(child=serializers.CharField()), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)

class ValidateUserAccessLabRoomSerializer(ValidateUserAccessOrgLabSerializer):
    lab_room = serializers.PrimaryKeyRelatedField(many=True, queryset=LaboratoryRoom.objects.using(settings.READONLY_DATABASE), allow_null=True, required=False)
    all_labs_org = serializers.BooleanField(default=False)