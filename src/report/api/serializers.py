from rest_framework import serializers
from django.conf import settings
from auth_and_perms.api.serializers import ValidateUserAccessOrgLabSerializer
from laboratory.models import LaboratoryRoom, Laboratory, Object, Catalog, \
    ShelfObject
from report.models import ObjectChangeLogReportBuilder
from django.utils.translation import gettext_lazy as _
import logging
logger = logging.getLogger('organilab')


class ReportDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=serializers.ListSerializer(child=serializers.CharField()), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)

class ValidateUserAccessLabRoomSerializer(ValidateUserAccessOrgLabSerializer):
    lab_room = serializers.PrimaryKeyRelatedField(many=True, queryset=LaboratoryRoom.objects.using(settings.READONLY_DATABASE), allow_null=True, required=False)
    all_labs_org = serializers.BooleanField(default=False)
    shelfobject = serializers.PrimaryKeyRelatedField(
        queryset=ShelfObject.objects.using(settings.READONLY_DATABASE), allow_null=True,
        required=False)


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
        return ''


    class Meta:
        model = ObjectChangeLogReportBuilder
        fields = '__all__'

class ObjectChangeDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ObjectChangeLogSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)

class ValidateObjectChangeFilters(serializers.Serializer):
    laboratory = serializers.PrimaryKeyRelatedField(
        queryset=Laboratory.objects.all().using(settings.READONLY_DATABASE))
    object = serializers.PrimaryKeyRelatedField(
        queryset=Object.objects.all().using(settings.READONLY_DATABASE))
    unit = serializers.PrimaryKeyRelatedField(
        queryset=Catalog.objects.filter(key='units').using(settings.READONLY_DATABASE))
