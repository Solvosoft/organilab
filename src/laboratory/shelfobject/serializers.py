from rest_framework import serializers

from laboratory.models import ShelfObject, Shelf, Catalog, Object, Laboratory


class AddShelfObjectSerializer(serializers.Serializer):
    amount = serializers.FloatField()
    bill = serializers.CharField(required=False)
    provider = serializers.IntegerField(required=False)
    shelf_object = serializers.IntegerField()


class SubstractShelfObjectSerializer(serializers.Serializer):
    discount = serializers.FloatField()
    description = serializers.CharField(required=False)
    shelf_object = serializers.IntegerField()


class ValidateShelfSerializer(serializers.Serializer):
    shelf = serializers.PrimaryKeyRelatedField(many=False, queryset=Shelf.objects.all())
    objecttype = serializers.ChoiceField(choices=(
        ("0", 'Reactive'),
        ("1", 'Material'),
        ("2", 'Equipment')), required=True)


class CreateShelfObjectSerializer(serializers.ModelSerializer):
    obj = serializers.PrimaryKeyRelatedField(many=False, queryset=Object.objects.all(), pk_field="object")
    shelf = serializers.PrimaryKeyRelatedField(many=False, queryset=Shelf.objects.all(), required=True)
    quantity = serializers.FloatField(required=True)
    limit_quantity: serializers.IntegerField(required=True)
    measurement_unit: serializers.PrimaryKeyRelatedField(many=False, queryset=Catalog.objects.all(), required=True)

    class Meta:
        model = ShelfObject
        fields = ['object', 'shelf', 'quantity', 'measurement_unit', 'limit_quantity']


class TransferOutShelfObjectSerializer(serializers.Serializer):
    shelf_object = serializers.PrimaryKeyRelatedField(queryset=ShelfObject.objects.all())
    amount_to_transfer = serializers.FloatField()
    mark_as_discard = serializers.BooleanField()
    laboratory = serializers.PrimaryKeyRelatedField(queryset=Laboratory.objects.all())
