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
#OrganizationStructure


class ObjectsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Object
        fields = '__all__'


class InformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inform
        fields = '__all__'


class LaboratorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Laboratory
        fields = '__all__'


class IncidentReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentReport
        fields = '__all__'


class OrganizationStrtSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationStructure
        fields = '__all__'

