from django.contrib.auth.models import User

from laboratory.models import Object, Inform, Laboratory, OrganizationStructure
from risk_management.models import IncidentReport
from rest_framework import serializers


class ObjectsSerializer(serializers.ModelSerializer):
    """
    Objects Model Serializer
    Serialize data into a key(id) and value(name)
    """
    key = serializers.ReadOnlyField(source='id')
    value = serializers.CharField(source='name')

    class Meta:
        model = Object
        fields = ['key', 'value']


class InformSerializer(serializers.ModelSerializer):
    """
    Inform Model Serializer
    Serialize data into a key(id) and value(name)
    """
    key = serializers.ReadOnlyField(source='id')
    value = serializers.CharField(source='name')

    class Meta:
        model = Inform
        fields = ['key', 'value']


class LaboratorySerializer(serializers.ModelSerializer):
    """
    Laboratory Model Serializer
    Serialize data into a key(id) and value(name)
    """
    key = serializers.ReadOnlyField(source='id')
    value = serializers.CharField(source='name')

    class Meta:
        model = Laboratory
        fields = ['key', 'value']


class IncidentReportSerializer(serializers.ModelSerializer):
    """
    Object Model Serializer
    Serialize data into a key(id) and value(short_description)
    """
    key = serializers.ReadOnlyField(source='id')
    value = serializers.CharField(source='short_description')

    class Meta:
        model = IncidentReport
        fields = ['key', 'value']


class OrganizationUsersSerializer(serializers.ModelSerializer):
    """
    OrganizationStructure Model Serializer
    Serialize data into users from organization
    """
    class Meta:
        model = OrganizationStructure
        fields = ['users']

class UsersSerializer(serializers.ModelSerializer):
    key = serializers.IntegerField(source='id')
    value = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['key', 'value']

    def get_value(self, obj):
        name = obj.get_full_name()
        if name:
            return name
        else:
            return obj.username