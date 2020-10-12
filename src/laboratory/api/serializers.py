from rest_framework import serializers
from reservations_management.models import ReservedProducts
from organilab.settings import DATETIME_INPUT_FORMATS


class ReservationSerializer(serializers.ModelSerializer):
    initial_date = serializers.DateTimeField(input_formats=[DATETIME_INPUT_FORMATS[0]], required=False)
    final_date = serializers.DateTimeField(input_formats=[DATETIME_INPUT_FORMATS[0]], required=False)

    class Meta:
        model = ReservedProducts
        fields = '__all__'
