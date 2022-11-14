from rest_framework import serializers

from auth_and_perms.models import AuthenticateDataRequest


class AuthenticateDataRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthenticateDataRequest
        fields = '__all__'
