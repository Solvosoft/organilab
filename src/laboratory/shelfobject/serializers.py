from django.conf import settings
import logging
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from laboratory.models import ShelfObject, Shelf, Catalog, Object, Laboratory, ShelfObjectLimits, ShelfObjectContainer

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
    OBJTYPE_CHOICES=(
        ("0", 'Reactive'),
        ("1", 'Material'),
        ("2", 'Equipment'))
    shelf = serializers.PrimaryKeyRelatedField(many=False, queryset=Shelf.objects.all())
    objecttype = serializers.ChoiceField(choices=OBJTYPE_CHOICES, required=True)

    def get_key_descriptor(self):
        """
        Atención debe llamar a is_valid() primero.
        :return:
        """
        names = {key: value.lower() for key, value in self.OBJTYPE_CHOICES}
        obj_type_name = names[self.validated_data['objecttype']]
        if self.validated_data['shelf'].discard:
            obj_type_name += "_refuse"
        return obj_type_name


class ShelfObjectLimitsSerializer(serializers.ModelSerializer):
    minimum_limit = serializers.FloatField(required=True)
    maximum_limit = serializers.FloatField(required=True)
    expiration_date = serializers.DateField(input_formats=settings.DATE_INPUT_FORMATS)

    class Meta:
        model = ShelfObjectLimits
        fields = '__all__'


class ReactiveShelfObjectSerializer(serializers.ModelSerializer):
    object = serializers.PrimaryKeyRelatedField(many=False, queryset=Object.objects.using(settings.READONLY_DATABASE),required=True)
    shelf = serializers.PrimaryKeyRelatedField(many=False, queryset=Shelf.objects.using(settings.READONLY_DATABASE), required=True)
    quantity = serializers.FloatField(required=True)
    limit_quantity= serializers.FloatField(required=True)
    measurement_unit= serializers.PrimaryKeyRelatedField(many=False, queryset=Catalog.objects.using(settings.READONLY_DATABASE), required=True)
    marked_as_discard = serializers.BooleanField(default=False, required=False)
    batch = serializers.CharField(required=True)

    class Meta:
        model = ShelfObject
        fields = ['object', 'shelf', 'quantity', 'measurement_unit', 'limit_quantity', 'marked_as_discard','batch']


class ReactiveRefuseShelfObjectSerializer(serializers.ModelSerializer):
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


class MaterialShelfObjectSerializer(serializers.ModelSerializer):
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


class MaterialRefuseShelfObjectSerializer(serializers.ModelSerializer):
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


class EquipmentShelfObjectSerializer(serializers.ModelSerializer):
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


class EquipmentRefuseShelfObjectSerializer(serializers.ModelSerializer):
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
            logger.debug(f'TransferOutShelfObjectSerializer --> attr.in_where_laboratory_id '
                         f'({attr.in_where_laboratory_id}) != source_laboratory_id ({source_laboratory_id})') 
            raise serializers.ValidationError(_("Object does not exist in the laboratory"))
        return attr

class ShelfObjectDeleteSerializer(serializers.Serializer):
    shelfobj = serializers.PrimaryKeyRelatedField(queryset=ShelfObject.objects.all())

    def validate_shelfobj(self, value):
        attr = super().validate(value)
        if attr.in_where_laboratory_id != self.context.get('laboratory_id'):
            logger.debug(f'ShelfObjectDeleteSerializer --> attr.in_where_laboratory_id ({attr.in_where_laboratory_id}) '
                         f'!= laboratory_id ({self.context.get("laboratory_id")})')
            raise serializers.ValidationError(_("Object does not exist in the laboratory"))
        return attr

class ShelfObjectContainerSerializer(serializers.ModelSerializer):
    container = serializers.PrimaryKeyRelatedField(many=False, queryset=Object.objects.filter(type=1).using(settings.READONLY_DATABASE), required=True)
    shelf_object = serializers.PrimaryKeyRelatedField(queryset=ShelfObject.objects.all())

    class Meta:
        model = ShelfObjectContainer
        fields ='__all__'

class ShelfObjectStatusSerializer(serializers.Serializer):
    description = serializers.CharField(allow_blank=False,required=True)

