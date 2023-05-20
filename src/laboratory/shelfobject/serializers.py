import logging

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from laboratory.models import Provider
from laboratory.models import REQUESTED
from laboratory.models import ShelfObject, Shelf, Catalog, Object, Laboratory, ShelfObjectLimits, ShelfObjectContainer, \
    TranferObject
from organilab.settings import DATETIME_INPUT_FORMATS
from reservations_management.models import ReservedProducts

logger = logging.getLogger('organilab')

class ReserveShelfObjectSerializer(serializers.ModelSerializer):
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
        if initial_date >= final_date:
            raise serializers.ValidationError({'initial_date':_("Initial date can't be greater than final date")})
        elif initial_date <= current_date:
            raise serializers.ValidationError({'initial_date':_("Initial date can't be equal or lower to current date")})
        elif initial_date <= current_date:
            raise serializers.ValidationError({'initial_date':_("Initial date can't be lower than current date")})
        elif final_date <= current_date:
            raise serializers.ValidationError({'initial_date': _("Final date can't be lower than current date")})

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
    amount = serializers.FloatField()
    bill = serializers.CharField(required=False)
    provider = serializers.IntegerField(required=False)
    shelf_object = serializers.IntegerField()


class IncreaseShelfObjectSerializer(serializers.Serializer):
    amount = serializers.FloatField(min_value=0.1)
    bill = serializers.CharField(required=False, allow_blank=True)
    provider = serializers.PrimaryKeyRelatedField(queryset=Provider.objects.all(), required=False, allow_null=True)
    shelf_object = serializers.PrimaryKeyRelatedField(queryset=ShelfObject.objects.all())

    def validate_shelf_object(self, value):
        attr = super().validate(value)
        source_laboratory_id = self.context.get("source_laboratory_id")
        if attr.in_where_laboratory_id != source_laboratory_id:
            logger.debug(
                f'AddShelfObjectSerializer --> attr.in_where_laboratory_id ({attr.in_where_laboratory_id}) != source_laboratory_id ({source_laboratory_id})')
            raise serializers.ValidationError(_("Object does not exist in the laboratory"))
        return attr

    def validate_provider(self, value):
        attr = super().validate(value)
        source_laboratory_id = self.context.get("source_laboratory_id")
        if attr:
            if not attr.laboratory != source_laboratory_id:
                logger.debug(
                    f'AddShelfObjectSerializer --> attr.laboratory ({attr.laboratory}) != source_laboratory_id ({source_laboratory_id})')
                raise serializers.ValidationError(_("Provider does not exist in the laboratory"))
        return attr


class DecreaseShelfObjectSerializer(serializers.Serializer):
    discount = serializers.FloatField(min_value=0.1)
    description = serializers.CharField(required=False, allow_blank=True)
    shelf_object = serializers.PrimaryKeyRelatedField(queryset=ShelfObject.objects.all())

    def validate_shelf_object(self, value):
        attr = super().validate(value)
        source_laboratory_id = self.context.get("source_laboratory_id")
        if attr.in_where_laboratory_id != source_laboratory_id:
            logger.debug(
                f'SubstractShelfObjectSerializer --> attr.in_where_laboratory_id ({attr.in_where_laboratory_id}) != source_laboratory_id ({source_laboratory_id})')
            raise serializers.ValidationError(_("Object does not exist in the laboratory"))
        return attr


class ValidateShelfSerializer(serializers.Serializer):
    OBJTYPE_CHOICES = (
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


class DateFieldWithEmptyString(serializers.DateField):
    def to_internal_value(self, value):
        if not value:
            return None
        return super(DateFieldWithEmptyString, self).to_internal_value(value)


class ShelfObjectLimitsSerializer(serializers.ModelSerializer):
    minimum_limit = serializers.FloatField(min_value=0.0, required=True, initial=0.0)
    maximum_limit = serializers.FloatField(min_value=0.0, required=True, initial=0.0)
    expiration_date = DateFieldWithEmptyString(input_formats=settings.DATE_INPUT_FORMATS, required=False,
                                               allow_null=True)

    class Meta:
        model = ShelfObjectLimits
        fields = '__all__'

    def validate(self, data):
        attr = super().validate(data)
        if attr['minimum_limit'] > attr['maximum_limit']:
            raise serializers.ValidationError(_("Minimum limit can't be greater than maximum limit"))
        return data


class ContainerShelfObjectSerializer(serializers.Serializer):
    container = serializers.PrimaryKeyRelatedField(many=False,
                                                   queryset=Object.objects.filter(type=1).using(
                                                       settings.READONLY_DATABASE),
                                                   required=True)


class ReactiveShelfObjectSerializer(serializers.ModelSerializer):
    object = serializers.PrimaryKeyRelatedField(many=False, queryset=Object.objects.using(settings.READONLY_DATABASE),
                                                required=True)
    shelf = serializers.PrimaryKeyRelatedField(many=False, queryset=Shelf.objects.using(settings.READONLY_DATABASE),
                                               required=True)
    quantity = serializers.FloatField(required=True)
    measurement_unit = serializers.PrimaryKeyRelatedField(many=False,
                                                          queryset=Catalog.objects.using(settings.READONLY_DATABASE),
                                                          required=True)
    marked_as_discard = serializers.BooleanField(default=False, required=False)
    batch = serializers.CharField(required=True)

    class Meta:
        model = ShelfObject
        fields = ['object', 'shelf', "status", 'quantity', 'measurement_unit', 'limit_quantity', "course_name",
                  'marked_as_discard', 'batch']


class ReactiveRefuseShelfObjectSerializer(serializers.ModelSerializer):
    object = serializers.PrimaryKeyRelatedField(many=False, queryset=Object.objects.using(settings.READONLY_DATABASE))
    shelf = serializers.PrimaryKeyRelatedField(many=False, queryset=Shelf.objects.using(settings.READONLY_DATABASE),
                                               required=True)
    status = serializers.PrimaryKeyRelatedField(many=False, queryset=Catalog.objects.using(settings.READONLY_DATABASE),
                                                required=True)
    quantity = serializers.FloatField(required=True)
    measurement_unit = serializers.PrimaryKeyRelatedField(many=False,
                                                          queryset=Catalog.objects.using(settings.READONLY_DATABASE),
                                                          required=True)
    marked_as_discard = serializers.BooleanField(default=True, required=False)
    course_name = serializers.CharField(required=False)
    batch = serializers.CharField(required=True)

    class Meta:
        model = ShelfObject
        fields = ["object", "shelf", "status", "quantity",
                  "measurement_unit", "marked_as_discard", "course_name", 'batch']


class MaterialShelfObjectSerializer(serializers.ModelSerializer):
    object = serializers.PrimaryKeyRelatedField(many=False, queryset=Object.objects.using(settings.READONLY_DATABASE))
    shelf = serializers.PrimaryKeyRelatedField(many=False, queryset=Shelf.objects.using(settings.READONLY_DATABASE),
                                               required=True)
    status = serializers.PrimaryKeyRelatedField(many=False, queryset=Catalog.objects.using(settings.READONLY_DATABASE),
                                                required=True)
    quantity = serializers.FloatField(required=True)
    limit_quantity = serializers.FloatField(required=True)
    measurement_unit = serializers.PrimaryKeyRelatedField(many=False,
                                                          queryset=Catalog.objects.using(settings.READONLY_DATABASE),
                                                          required=True)
    marked_as_discard = serializers.BooleanField(default=False, required=False)
    course_name = serializers.CharField(required=False)

    class Meta:
        model = ShelfObject
        fields = ["object", "shelf", "status", "quantity", "limit_quantity", "measurement_unit", "marked_as_discard",
                  "course_name"]


class MaterialRefuseShelfObjectSerializer(serializers.ModelSerializer):
    object = serializers.PrimaryKeyRelatedField(many=False, queryset=Object.objects.using(settings.READONLY_DATABASE))
    shelf = serializers.PrimaryKeyRelatedField(many=False, queryset=Shelf.objects.using(settings.READONLY_DATABASE),
                                               required=True)
    status = serializers.PrimaryKeyRelatedField(many=False, queryset=Catalog.objects.using(settings.READONLY_DATABASE),
                                                required=True)
    quantity = serializers.FloatField(required=True)
    limit_quantity = serializers.FloatField(required=True)
    measurement_unit = serializers.PrimaryKeyRelatedField(many=False,
                                                          queryset=Catalog.objects.using(settings.READONLY_DATABASE),
                                                          required=True)
    marked_as_discard = serializers.BooleanField(default=False, required=False)
    course_name = serializers.CharField(required=False)

    class Meta:
        model = ShelfObject
        fields = ["object", "shelf", "status", "quantity", "limit_quantity", "measurement_unit", "marked_as_discard",
                  "course_name"]


class EquipmentShelfObjectSerializer(serializers.ModelSerializer):
    object = serializers.PrimaryKeyRelatedField(many=False, queryset=Object.objects.using(settings.READONLY_DATABASE))
    shelf = serializers.PrimaryKeyRelatedField(many=False, queryset=Shelf.objects.using(settings.READONLY_DATABASE),
                                               required=True)
    status = serializers.PrimaryKeyRelatedField(many=False, queryset=Catalog.objects.using(settings.READONLY_DATABASE),
                                                required=True)
    quantity = serializers.FloatField(required=True)
    limit_quantity = serializers.FloatField(required=True)
    measurement_unit = serializers.PrimaryKeyRelatedField(many=False,
                                                          queryset=Catalog.objects.using(settings.READONLY_DATABASE),
                                                          required=True)
    marked_as_discard = serializers.BooleanField(default=False, required=False)
    course_name = serializers.CharField(required=False)

    class Meta:
        model = ShelfObject
        fields = ["object", "shelf", "status", "quantity", "limit_quantity", "measurement_unit", "marked_as_discard",
                  "course_name"]


class EquipmentRefuseShelfObjectSerializer(serializers.ModelSerializer):
    object = serializers.PrimaryKeyRelatedField(many=False, queryset=Object.objects.using(settings.READONLY_DATABASE))
    shelf = serializers.PrimaryKeyRelatedField(many=False, queryset=Shelf.objects.using(settings.READONLY_DATABASE),
                                               required=True)
    status = serializers.PrimaryKeyRelatedField(many=False, queryset=Catalog.objects.using(settings.READONLY_DATABASE),
                                                required=True)
    quantity = serializers.FloatField(required=True)
    limit_quantity = serializers.FloatField(required=True)
    measurement_unit = serializers.PrimaryKeyRelatedField(many=False,
                                                          queryset=Catalog.objects.using(settings.READONLY_DATABASE),
                                                          required=True)
    marked_as_discard = serializers.BooleanField(default=False, required=False)
    course_name = serializers.CharField(required=False)

    class Meta:
        model = ShelfObject
        fields = ["object", "shelf", "status", "quantity", "limit_quantity", "measurement_unit", "marked_as_discard",
                  "course_name"]


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


class ValidateShelfSerializer(serializers.Serializer):
    shelf = serializers.PrimaryKeyRelatedField(queryset=Shelf.objects.all())

    def validate_shelf(self, value):
        attr = super().validate(value)
        source_laboratory_id = self.context.get("source_laboratory_id")
        if attr.furniture.labroom.laboratory_id != source_laboratory_id:
            logger.debug(f'ValidateShelfSerializer --> attr.in_where_laboratory_id '
                         f'({attr.in_where_laboratory_id}) != source_laboratory_id ({source_laboratory_id})')
            raise serializers.ValidationError(_("Object does not exist in the laboratory"))
        return attr

class ShelfSerializer(serializers.ModelSerializer):

    type = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()
    quantity_storage_status = serializers.SerializerMethodField()
    percentage_storage_status = serializers.SerializerMethodField()
    shelf_info = serializers.SerializerMethodField()

    def get_type(self, obj):
        return str(obj.type) if obj.type else ""

    def get_quantity(self, obj):
        quantity = obj.quantity
        if quantity == -1:
            quantity = _("Unlimited storage")
        return quantity

    def get_measurement_unit(self, obj):
        return obj.get_measurement_unit_display()

    def get_quantity_storage_status(self, obj):
        return f'{obj.get_total_refuse()} {_("of")} {obj.quantity}'

    def get_percentage_storage_status(self, obj):
        return f'{obj.get_refuse_porcentage()}% {_("of")} 100%'

    def get_shelf_info(self, obj):
        shelf = {
            'name': obj.name,
            'type': self.get_type(obj),
            'quantity': self.get_quantity(obj),
            'discard': obj.discard,
            'measurement_unit': self.get_measurement_unit(obj),
            'quantity_storage_status': self.get_quantity_storage_status(obj),
            'percentage_storage_status': self.get_percentage_storage_status(obj)
        }
        return render_to_string(
            'laboratory/shelfobject/shelf_availability_information.html',
            context={'shelf': shelf}
        )

    class Meta:
        model = Shelf
        fields = ['name', 'type', 'quantity', 'discard', 'measurement_unit', 'quantity_storage_status', 'shelf_info',
                  'percentage_storage_status']

class ShelfObjectContainerSerializer(serializers.ModelSerializer):
    container = serializers.PrimaryKeyRelatedField(many=False, queryset=Object.objects.filter(type=1).using(
        settings.READONLY_DATABASE), required=True)
    shelf_object = serializers.PrimaryKeyRelatedField(queryset=ShelfObject.objects.all())

    class Meta:
        model = ShelfObjectContainer
        fields = '__all__'


class ShelfObjectStatusSerializer(serializers.Serializer):
    description = serializers.CharField(allow_blank=False, required=True)


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
