from rest_framework import serializers
from reservations_management.models import ReservedProducts, Reservations
from organilab.settings import DATETIME_INPUT_FORMATS


class ReservedProductsSerializer(serializers.ModelSerializer):
    initial_date = serializers.DateTimeField(input_formats=[DATETIME_INPUT_FORMATS[0]], required=False)
    final_date = serializers.DateTimeField(input_formats=[DATETIME_INPUT_FORMATS[0]], required=False)

    class Meta:
        model = ReservedProducts
        fields = '__all__'


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservations
        fields = '__all__'
