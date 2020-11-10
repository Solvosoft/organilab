from rest_framework import serializers
from reservations_management.models import ReservedProducts, Reservations
from laboratory.models import ShelfObject


class ReservedProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReservedProducts
        fields = '__all__'
