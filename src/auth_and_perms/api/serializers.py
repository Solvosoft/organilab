from rest_framework import serializers
from rest_framework.reverse import reverse_lazy

from auth_and_perms.models import Rol, Profile, AuthenticateDataRequest
from laboratory.models import OrganizationStructure


class RolSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)

    class Meta:
        model = Rol
        fields = ["name", "permissions"]


class AuthenticateDataRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthenticateDataRequest
        fields = '__all__'

class AuthenticateDataRequestNotifySerializer(serializers.Serializer):
    id_transaction = serializers.IntegerField()
    data = AuthenticateDataRequestSerializer()

class ContentTypeObjectToPermissionManager(serializers.Serializer):
    org=serializers.PrimaryKeyRelatedField(queryset=OrganizationStructure.objects.all())
    appname = serializers.CharField()
    model = serializers.CharField()
    objectid = serializers.IntegerField(required=False, allow_null=True)


class ProfilePermissionRolOrganizationSerializer(serializers.Serializer):
    rols = serializers.PrimaryKeyRelatedField(many=True, queryset=Rol.objects.all())
    as_conttentype = serializers.BooleanField(required=True)
    as_user = serializers.BooleanField(required=True)
    as_role = serializers.BooleanField(required=True)
    profile = serializers.PrimaryKeyRelatedField(queryset=Profile.objects.all(), allow_null=True, required=False)
    contenttypeobj = ContentTypeObjectToPermissionManager(allow_null=True)
    mergeaction = serializers.ChoiceField(choices=[
        ('append', reverse_lazy('Append')), ('sustract', reverse_lazy('Sustract')),
        ('full', reverse_lazy('Only roles selected'))
    ])



class OrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrganizationStructure
        fields = ['name', 'parent']

