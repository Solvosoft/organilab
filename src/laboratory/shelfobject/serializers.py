import logging
from django.utils.timezone import now
from rest_framework import serializers
from organilab.settings import DATETIME_INPUT_FORMATS
from laboratory.models import Laboratory, ShelfObject, Provider
from reservations_management.models import ReservedProducts
from django.utils.translation import gettext_lazy as _
logger = logging.getLogger('organilab')

class ReservedShelfObjectSerializer(serializers.ModelSerializer):
    amount_required = serializers.FloatField(min_value=0.1)
    shelf_object = serializers.PrimaryKeyRelatedField(queryset=ShelfObject.objects.all())
    initial_date = serializers.DateTimeField(input_formats=DATETIME_INPUT_FORMATS)
    final_date = serializers.DateTimeField(input_formats=DATETIME_INPUT_FORMATS)

    def validate(self, data):
        current_date = now().date()
        initial_date = data['initial_date'].date()
        final_date = data['final_date'].date()

        if initial_date == final_date:
            raise serializers.ValidationError({'final_date':_("Final date can't be equal to initial date")})
        if not initial_date < final_date:
            raise serializers.ValidationError({'initial_date':_("Initial date can't be greater than final date")})
        elif not initial_date != current_date:
            raise serializers.ValidationError({'initial_date':_("Initial date can't be equal to current date")})
        elif not initial_date > current_date:
            raise serializers.ValidationError({'initial_date':_("Initial date can't be lower than current date")})
        return data

    def validate_shelf_object(self, value):
        attr = super().validate(value)
        source_laboratory_id = self.context.get("source_laboratory_id")
        if attr.in_where_laboratory_id != source_laboratory_id:
            logger.debug(
                f'ReservedShelfObjectSerializer --> attr.in_where_laboratory_id ({attr.in_where_laboratory_id}) != source_laboratory_id ({source_laboratory_id})')
            raise serializers.ValidationError(_("Object does not exist in the laboratory"))
        return attr

    class Meta:
        model = ReservedProducts
        fields = ['amount_required', 'shelf_object', 'initial_date', 'final_date']


class AddShelfObjectSerializer(serializers.Serializer):
    amount = serializers.FloatField(min_value=0.1)
    bill = serializers.CharField(required=False)
    provider = serializers.PrimaryKeyRelatedField(queryset=Provider.objects.all(), required=False)
    shelf_object = serializers.PrimaryKeyRelatedField(queryset=ShelfObject.objects.all())


class SubstractShelfObjectSerializer(serializers.Serializer):
    discount = serializers.FloatField(min_value=0.1)
    description = serializers.CharField(required=False)
    shelf_object = serializers.PrimaryKeyRelatedField(queryset=ShelfObject.objects.all())


class TransferOutShelfObjectSerializer(serializers.Serializer):
    shelf_object = serializers.PrimaryKeyRelatedField(queryset=ShelfObject.objects.all())
    amount_to_transfer = serializers.FloatField(min_value=0.1)
    mark_as_discard = serializers.BooleanField(default=False)
    laboratory = serializers.PrimaryKeyRelatedField(queryset=Laboratory.objects.all())
