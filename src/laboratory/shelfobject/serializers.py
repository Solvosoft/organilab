import logging

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from laboratory.models import Laboratory, ShelfObject, TranferObject, REQUESTED

logger = logging.getLogger('organilab')

class AddShelfObjectSerializer(serializers.Serializer):
    amount = serializers.FloatField()
    bill = serializers.CharField(required=False)
    provider = serializers.IntegerField(required=False)
    shelf_object = serializers.IntegerField()


class SubstractShelfObjectSerializer(serializers.Serializer):
    discount = serializers.FloatField()
    description = serializers.CharField(required=False)
    shelf_object = serializers.IntegerField()


class TransferOutShelfObjectSerializer(serializers.Serializer):
    shelf_object = serializers.PrimaryKeyRelatedField(queryset=ShelfObject.objects.all())
    amount_to_transfer = serializers.FloatField(min_value=0.1)
    mark_as_discard = serializers.BooleanField(default=False)
    laboratory = serializers.PrimaryKeyRelatedField(queryset=Laboratory.objects.all())
    
    def validate_shelf_object(self, value):
        attr = super().validate(value)
        source_laboratory_id = self.context.get("source_laboratory_id")
        if attr.in_where_laboratory_id != source_laboratory_id:
            logger.debug(f'TransferOutShelfObjectSerializer --> attr.in_where_laboratory_id '
                         f'({attr.in_where_laboratory_id}) != source_laboratory_id ({source_laboratory_id})') 
            raise serializers.ValidationError(_("Object does not exist in the laboratory."))
        return attr

class ShelfObjectDeleteSerializer(serializers.Serializer):
    shelfobj = serializers.PrimaryKeyRelatedField(queryset=ShelfObject.objects.all())

    def validate_shelfobj(self, value):
        attr = super().validate(value)
        if attr.in_where_laboratory_id != self.context.get('laboratory_id'):
            logger.debug(f'ShelfObjectDeleteSerializer --> attr.in_where_laboratory_id ({attr.in_where_laboratory_id}) '
                         f'!= laboratory_id ({self.context.get("laboratory_id")})')
            raise serializers.ValidationError(_("Object does not exist in the laboratory."))
        return attr

class TransferObjectSerializer(serializers.ModelSerializer):
    object = serializers.SerializerMethodField()
    laboratory_send = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    
    def get_object(self, obj):
        return obj.object.object.name
    
    def get_laboratory_send(self, obj):
        return obj.laboratory_send.name
    
    def get_quantity(self, obj):
        return f"{obj.quantity} {obj.object.get_measurement_unit_display()}"
    
    class Meta:
        model = TranferObject
        fields = ("id", "object", "quantity", "laboratory_send", "update_time", "mark_as_discard")
    
    
class TransferObjectDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=TransferObjectSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)

class TransferObjectDenySerializer(serializers.Serializer):
    transfer_object = serializers.PrimaryKeyRelatedField(queryset=TranferObject.objects.filter(status=REQUESTED))

    def validate_transfer_object(self, value):
        attr = super().validate(value)
        if attr.laboratory_received_id != self.context.get('laboratory_id'):
            logger.debug(f'TransferObjectDeleteSerializer --> attr.laboratory_received ({attr.laboratory_received}) '
                         f'!= laboratory_id ({self.context.get("laboratory_id")})')
            raise serializers.ValidationError(_("Transfer was not sent to the laboratory."))
        return attr