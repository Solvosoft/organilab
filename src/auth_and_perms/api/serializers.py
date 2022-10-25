from rest_framework import serializers

from auth_and_perms.models import Rol


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ["name"]