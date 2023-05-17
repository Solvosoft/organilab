from django.conf import settings
import logging
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from laboratory.models import ShelfObject, Shelf, Catalog, Object, Laboratory, ShelfObjectLimits

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


class ValidateShelfSerializer(serializers.Serializer):
    shelf = serializers.PrimaryKeyRelatedField(many=False, queryset=Shelf.objects.all())
    objecttype = serializers.ChoiceField(choices=(
        ("0", 'Reactive'),
        ("1", 'Material'),
        ("2", 'Equipment')), required=True)


class ReactiveShelfObjectSerializer(serializers.Serializer):
    object = serializers.PrimaryKeyRelatedField(many=False, queryset=Object.objects.using(settings.READONLY_DATABASE))
    shelf = serializers.PrimaryKeyRelatedField(many=False, queryset=Shelf.objects.using(settings.READONLY_DATABASE), required=True)
    quantity = serializers.FloatField(required=True)
    limit_quantity= serializers.CharField(required=True)
    measurement_unit= serializers.PrimaryKeyRelatedField(many=False, queryset=Catalog.objects.using(settings.READONLY_DATABASE), required=True)
    limits = serializers.PrimaryKeyRelatedField(many=False, queryset=ShelfObjectLimits.objects.using(settings.READONLY_DATABASE), required=True)
    marked_as_discard = serializers.BooleanField(default=False, required=False)
    batch = serializers.CharField(required=True)

    class Meta:
        model = ShelfObject
        fields = ['object', 'shelf', 'quantity', 'measurement_unit', 'limit_quantity', 'limits', 'marked_as_discard','batch']


class ReactiveRefuseShelfObjectSerializer(serializers.Serializer):
    object = serializers.PrimaryKeyRelatedField(many=False, queryset=Object.objects.using(settings.READONLY_DATABASE))
    shelf = serializers.PrimaryKeyRelatedField(many=False, queryset=Shelf.objects.using(settings.READONLY_DATABASE), required=True)
    status = serializers.PrimaryKeyRelatedField(many=False, queryset=Catalog.objects.using(settings.READONLY_DATABASE), required=True)
    quantity = serializers.FloatField(required=True)
    limit_quantity= serializers.FloatField(required=True)
    measurement_unit= serializers.PrimaryKeyRelatedField(many=False, queryset=Catalog.objects.using(settings.READONLY_DATABASE), required=True)
    limits = serializers.PrimaryKeyRelatedField(many=False, queryset=ShelfObjectLimits.objects.using(settings.READONLY_DATABASE), required=True)
    marked_as_discard = serializers.BooleanField(default=True, required=False)
    course_name = serializers.CharField(required=False)

    class Meta:
        model = ShelfObject
        fields = ["object","shelf","status","quantity","limit_quantity","measurement_unit","marked_as_discard","course_name","limits"]

class MaterialShelfObjectSerializer(serializers.Serializer):
    object = serializers.PrimaryKeyRelatedField(many=False, queryset=Object.objects.using(settings.READONLY_DATABASE))
    shelf = serializers.PrimaryKeyRelatedField(many=False, queryset=Shelf.objects.using(settings.READONLY_DATABASE), required=True)
    status = serializers.PrimaryKeyRelatedField(many=False, queryset=Catalog.objects.using(settings.READONLY_DATABASE), required=True)
    quantity = serializers.FloatField(required=True)
    limit_quantity= serializers.FloatField(required=True)
    measurement_unit= serializers.PrimaryKeyRelatedField(many=False, queryset=Catalog.objects.using(settings.READONLY_DATABASE), required=True)
    limits = serializers.PrimaryKeyRelatedField(many=False, queryset=ShelfObjectLimits.objects.using(settings.READONLY_DATABASE), required=True)
    marked_as_discard = serializers.BooleanField(default=False, required=False)
    course_name = serializers.CharField(required=False)

    class Meta:
        model = ShelfObject
        fields = ["object","shelf","status","quantity","limit_quantity","measurement_unit","marked_as_discard","course_name","limits"]

class MaterialRefuseShelfObjectSerializer(serializers.Serializer):
    object = serializers.PrimaryKeyRelatedField(many=False, queryset=Object.objects.using(settings.READONLY_DATABASE))
    shelf = serializers.PrimaryKeyRelatedField(many=False, queryset=Shelf.objects.using(settings.READONLY_DATABASE), required=True)
    status = serializers.PrimaryKeyRelatedField(many=False, queryset=Catalog.objects.using(settings.READONLY_DATABASE), required=True)
    quantity = serializers.FloatField(required=True)
    limit_quantity= serializers.FloatField(required=True)
    measurement_unit= serializers.PrimaryKeyRelatedField(many=False, queryset=Catalog.objects.using(settings.READONLY_DATABASE), required=True)
    limits = serializers.PrimaryKeyRelatedField(many=False, queryset=ShelfObjectLimits.objects.using(settings.READONLY_DATABASE), required=True)
    marked_as_discard = serializers.BooleanField(default=False, required=False)
    course_name = serializers.CharField(required=False)

    class Meta:
        model = ShelfObject
        fields = ["object","shelf","status","quantity","limit_quantity","measurement_unit","marked_as_discard","course_name","limits"]

class EquipmentShelfObjectSerializer(serializers.Serializer):
    object = serializers.PrimaryKeyRelatedField(many=False, queryset=Object.objects.using(settings.READONLY_DATABASE))
    shelf = serializers.PrimaryKeyRelatedField(many=False, queryset=Shelf.objects.using(settings.READONLY_DATABASE), required=True)
    status = serializers.PrimaryKeyRelatedField(many=False, queryset=Catalog.objects.using(settings.READONLY_DATABASE), required=True)
    quantity = serializers.FloatField(required=True)
    limit_quantity= serializers.FloatField(required=True)
    measurement_unit= serializers.PrimaryKeyRelatedField(many=False, queryset=Catalog.objects.using(settings.READONLY_DATABASE), required=True)
    limits = serializers.PrimaryKeyRelatedField(many=False, queryset=ShelfObjectLimits.objects.using(settings.READONLY_DATABASE), required=True)
    marked_as_discard = serializers.BooleanField(default=False, required=False)
    course_name = serializers.CharField(required=False)

    class Meta:
        model = ShelfObject
        fields = ["object","shelf","status","quantity","limit_quantity","measurement_unit","marked_as_discard","course_name","limits"]

class EquipmentRefuseShelfObjectSerializer(serializers.Serializer):
    object = serializers.PrimaryKeyRelatedField(many=False, queryset=Object.objects.using(settings.READONLY_DATABASE))
    shelf = serializers.PrimaryKeyRelatedField(many=False, queryset=Shelf.objects.using(settings.READONLY_DATABASE), required=True)
    status = serializers.PrimaryKeyRelatedField(many=False, queryset=Catalog.objects.using(settings.READONLY_DATABASE), required=True)
    quantity = serializers.FloatField(required=True)
    limit_quantity= serializers.FloatField(required=True)
    measurement_unit= serializers.PrimaryKeyRelatedField(many=False, queryset=Catalog.objects.using(settings.READONLY_DATABASE), required=True)
    limits = serializers.PrimaryKeyRelatedField(many=False, queryset=ShelfObjectLimits.objects.using(settings.READONLY_DATABASE), required=True)
    marked_as_discard = serializers.BooleanField(default=False, required=False)
    course_name = serializers.CharField(required=False)

    class Meta:
        model = ShelfObject
        fields = ["object","shelf","status","quantity","limit_quantity","measurement_unit","marked_as_discard","course_name","limits"]


class TransferOutShelfObjectSerializer(serializers.Serializer):
    shelf_object = serializers.PrimaryKeyRelatedField(queryset=ShelfObject.objects.all())
    amount_to_transfer = serializers.FloatField(min_value=0.1)
    mark_as_discard = serializers.BooleanField(default=False)
    laboratory = serializers.PrimaryKeyRelatedField(queryset=Laboratory.objects.all())
    
    def validate_shelf_object(self, value):
        attr = super().validate(value)
        source_laboratory_id = self.context.get("source_laboratory_id")
        if attr.in_where_laboratory_id != source_laboratory_id:
            logger.debug(f'TransferOutShelfObjectSerializer --> attr.in_where_laboratory_id ({attr.in_where_laboratory_id}) != source_laboratory_id ({source_laboratory_id})') 
            raise serializers.ValidationError(_("Object does not exist in the laboratory"))
        return attr
