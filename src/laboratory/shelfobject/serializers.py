from rest_framework import serializers

from laboratory.models import Laboratory, ShelfObject, Provider


class AddShelfObjectSerializer(serializers.Serializer):
    amount = serializers.FloatField(min_value=0.1)
    bill = serializers.CharField(required=False)
    provider = serializers.PrimaryKeyRelatedField(queryset=Provider.objects.all())
    shelf_object = serializers.PrimaryKeyRelatedField(queryset=ShelfObject.objects.all())


class SubstractShelfObjectSerializer(serializers.Serializer):
    discount = serializers.FloatField(min_value=0.1)
    description = serializers.CharField(required=False)
    shelf_object = serializers.PrimaryKeyRelatedField(queryset=ShelfObject.objects.all())


class TransferOutShelfObjectSerializer(serializers.Serializer):
    shelf_object = serializers.PrimaryKeyRelatedField(queryset=ShelfObject.objects.all())
    amount_to_transfer = serializers.FloatField()
    mark_as_discard = serializers.BooleanField()
    laboratory = serializers.PrimaryKeyRelatedField(queryset=Laboratory.objects.all())
