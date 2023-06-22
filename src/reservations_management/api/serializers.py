from rest_framework import serializers
from reservations_management.models import ReservedProducts, Reservations
from laboratory.models import ShelfObject
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import logging

logger = logging.getLogger('organilab')

class ReservedProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReservedProducts
        fields = '__all__'


class ValidateReservedProductsSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=ReservedProducts.objects.using(settings.READONLY_DATABASE))

    def validate_id(self, value):
        attr = super().validate(value)
        organization_id = self.context.get("organization_id")
        if attr.organization_id != organization_id:
            logger.debug(
                f'ValidateRPSerializer --> attr.organization_id ({attr.organization_id}) != organization_id ({organization_id})')
            raise serializers.ValidationError(_("Reserved product doesn't exists in this organization"))
        return attr

class ValidateReservedProductsAmountSerializer(ValidateReservedProductsSerializer):
    amount_to_return = serializers.FloatField(min_value=0.1)
