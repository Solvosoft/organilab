from auth_and_perms.organization_utils import user_is_allowed_on_organization, organization_can_change_laboratory
from laboratory.models import Object, Inform, Laboratory, OrganizationStructure
from laboratory.utils import get_users_from_organization
from risk_management.models import IncidentReport
from rest_framework import serializers

"""
user_is_allowed_on_organization()
organization_can_change_laboratory()
get_users_from_organization()
"""
#Item structure
#<option value={{item.key}}>{{item.value}}</option>


class ObjectsSerializer(serializers.ModelSerializer):
    key = serializers.ReadOnlyField(source='id')
    value = serializers.CharField(source='name')
    class Meta:
        model = Object
        fields = ['key', 'value']


class InformSerializer(serializers.ModelSerializer):
    key = serializers.ReadOnlyField(source='id')
    value = serializers.CharField(source='name')
    class Meta:
        model = Inform
        fields = ['key', 'value']


class LaboratorySerializer(serializers.ModelSerializer):
    key = serializers.ReadOnlyField(source='id')
    value = serializers.CharField(source='name')
    class Meta:
        model = Laboratory
        fields = ['key', 'value']


class IncidentReportSerializer(serializers.ModelSerializer):
    key = serializers.ReadOnlyField(source='id')
    value = serializers.CharField(source='short_description')

    class Meta:
        model = IncidentReport
        fields = ['key', 'value']


class OrganizationStrtSerializer(serializers.ModelSerializer):
    key = serializers.ReadOnlyField(source='id')
    value = serializers.CharField(source='name')
    class Meta:
        model = OrganizationStructure
        fields = ['key', 'value']

