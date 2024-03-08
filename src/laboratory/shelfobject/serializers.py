import logging
import re
from django.conf import settings
from django.contrib.auth.models import User
from django.forms import model_to_dict
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_filters import FilterSet
from djgentelella.fields.files import ChunkedFileField
from djgentelella.serializers.selects import GTS2SerializerBase

from auth_and_perms.api.serializers import ValidateUserAccessOrgLabSerializer
from auth_and_perms.models import Profile
from laboratory.api.serializers import BaseShelfObjectSerializer
from rest_framework import serializers
from laboratory.models import ShelfObject, Shelf, Catalog, Object, Laboratory, \
    ShelfObjectLimits, TranferObject, ShelfObjectObservation, Provider, \
    Furniture, LaboratoryRoom, SustanceCharacteristics, REQUESTED, \
    ShelfObjectMaintenance, OrganizationStructure, ShelfObjectLog, ShelfObjectCalibrate, \
    ShelfObjectGuarantee, ShelfObjectTraining
from laboratory.utils import get_actions_by_perms
from reservations_management.models import ReservedProducts
from laboratory.shelfobject.utils import get_available_containers_for_selection, \
    get_containers_for_cloning, get_shelf_queryset_by_filters, \
    get_furniture_queryset_by_filters, get_lab_room_queryset_by_filters, \
    limit_objects_by_shelf, validate_measurement_unit_and_quantity, \
    get_selected_container, group_object_errors_for_serializer
from djgentelella.serializers.selects import GTS2SerializerBase

logger = logging.getLogger('organilab')


class ValidateShelfSerializer(serializers.Serializer):
    shelf = serializers.PrimaryKeyRelatedField(
        queryset=Shelf.objects.using(settings.READONLY_DATABASE).order_by('pk'), required=True)

    def validate_shelf(self, value):
        attr = super().validate(value)
        laboratory_id = self.context.get("laboratory_id")
        if attr.furniture.labroom.laboratory_id != laboratory_id:
            logger.debug(
                f'ValidateShelfSerializer --> attr.furniture.labroom.laboratory_id '
                f'({attr.furniture.labroom.laboratory_id}) != laboratory_id ({laboratory_id})')
            raise serializers.ValidationError(
                _("Object does not exist in the laboratory."))
        return attr


class ContainerSerializer(ValidateShelfSerializer):
    # it inherits the shelf field and its validation from the parent serializer

    CONTAINER_SELECT_CHOICES = [
        ('clone', _('Create new based on selected')),
        ('available', _('Use selected')),
    ]
    container_select_option = serializers.ChoiceField(required=True,
                                                      choices=CONTAINER_SELECT_CHOICES)
    container_for_cloning = serializers.PrimaryKeyRelatedField(many=False,
                                                               allow_null=True,
                                                               queryset=Object.objects.none())
    available_container = serializers.PrimaryKeyRelatedField(many=False,
                                                             allow_null=True,
                                                             queryset=ShelfObject.objects.none())
    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        # allow select only available containers or containers for cloning depending on what the user wants and make the right field not nullable
        container_select_option = self.initial_data.get('container_select_option')
        if container_select_option == 'clone':
            # set queryset to validate that only those in the organization of type material are valid for selection
            fields['container_for_cloning'].queryset = get_containers_for_cloning(self.context['organization_id'],
                                                                                  self.initial_data.get('shelf'))
            fields['container_for_cloning'].allow_null = False
        elif container_select_option == 'available':
            # set queryset to validate that only those in the laboratory of type material are valid for selection
            fields['available_container'].queryset = get_available_containers_for_selection(self.context['laboratory_id'],
                                                                                            self.initial_data.get('shelf'))
            fields['available_container'].allow_null = False
        return fields

class ReserveShelfObjectSerializer(serializers.ModelSerializer):
    amount_required = serializers.FloatField(min_value=settings.DEFAULT_MIN_QUANTITY)
    shelf_object = serializers.PrimaryKeyRelatedField(
        queryset=ShelfObject.objects.using(settings.READONLY_DATABASE))
    initial_date = serializers.DateTimeField(input_formats=settings.DATETIME_INPUT_FORMATS)
    final_date = serializers.DateTimeField(input_formats=settings.DATETIME_INPUT_FORMATS)

    def validate(self, data):
        current_date = now().date()
        initial_date = data['initial_date'].date()
        final_date = data['final_date'].date()

        if initial_date == final_date:
            logger.debug(
                f'ReserveShelfObjectSerializer --> initial_date ({initial_date}) == final_date ({final_date})')
            raise serializers.ValidationError(
                {'final_date': _("Final date cannot be equal to initial date.")})
        if initial_date > final_date:
            logger.debug(
                f'ReserveShelfObjectSerializer --> initial_date ({initial_date}) > final_date ({final_date})')
            raise serializers.ValidationError(
                {'initial_date': _("Initial date cannot be greater than final date.")})
        elif initial_date <= current_date:
            logger.debug(
                f'ReserveShelfObjectSerializer --> initial_date ({initial_date}) <= current_date ({current_date})')
            raise serializers.ValidationError({'initial_date': _(
                "Initial date cannot be equal or lower than current date.")})
        elif final_date <= current_date:
            logger.debug(
                f'ReserveShelfObjectSerializer --> final_date ({final_date}) <= current_date ({current_date})')
            raise serializers.ValidationError({'final_date': _(
                "Final date cannot be equal or lower than current date.")})

        return data

    def validate_shelf_object(self, value):
        attr = super().validate(value)
        source_laboratory_id = self.context.get("source_laboratory_id")
        if attr.in_where_laboratory_id != source_laboratory_id:
            logger.debug(
                f'ReservedShelfObjectSerializer --> attr.in_where_laboratory_id ({attr.in_where_laboratory_id}) != '
                f'source_laboratory_id ({source_laboratory_id})')
            raise serializers.ValidationError(
                _("Object does not exist in the laboratory."))
        return attr

    class Meta:
        model = ReservedProducts
        fields = ['amount_required', 'shelf_object', 'initial_date', 'final_date']


class IncreaseShelfObjectSerializer(serializers.Serializer):
    amount = serializers.FloatField(min_value=settings.DEFAULT_MIN_QUANTITY)
    bill = serializers.CharField(required=False, allow_blank=True)
    provider = serializers.PrimaryKeyRelatedField(
        queryset=Provider.objects.using(settings.READONLY_DATABASE),
        required=False, allow_null=True)
    shelf_object = serializers.PrimaryKeyRelatedField(
        queryset=ShelfObject.objects.using(settings.READONLY_DATABASE))

    def validate_shelf_object(self, value):
        attr = super().validate(value)
        source_laboratory_id = self.context.get("source_laboratory_id")
        if attr.in_where_laboratory_id != source_laboratory_id:
            logger.debug(
                f'IncreaseShelfObjectSerializer --> attr.in_where_laboratory_id ({attr.in_where_laboratory_id}) != '
                f'source_laboratory_id ({source_laboratory_id})')
            raise serializers.ValidationError(
                _("Object does not exist in the laboratory."))
        return attr

    def validate_provider(self, value):
        attr = super().validate(value)
        source_laboratory_id = self.context.get("source_laboratory_id")
        if attr:
            if attr.laboratory_id != source_laboratory_id:
                logger.debug(
                    f'IncreaseShelfObjectSerializer --> attr.laboratory ({attr.laboratory}) != '
                    f'source_laboratory_id ({source_laboratory_id})')
                raise serializers.ValidationError(
                    _("Provider does not exist in the laboratory."))
        return attr

    def validate(self, data):
        data = super().validate(data)
        shelf_object = data['shelf_object']
        shelf = shelf_object.shelf
        amount = data['amount']
        measurement_unit = shelf_object.measurement_unit if shelf_object.object.type == Object.REACTIVE else None
        errors = validate_measurement_unit_and_quantity(shelf,
                                                        shelf_object.object,
                                                        amount,
                                                        measurement_unit=measurement_unit)

        if errors:
            updated_errors = {}
            shelfobject_errors = []
            amount_errors = []
            for key, error in errors.items():
                if key in ['object', 'measurement_unit']:
                    shelfobject_errors.append(error)
                elif key == 'quantity':
                    amount_errors.append(error)
                else:
                    updated_errors[key] = error
                if shelfobject_errors:
                    updated_errors['shelf_object'] = shelfobject_errors
                if amount_errors:
                    updated_errors['amount'] = amount_errors
            raise serializers.ValidationError(updated_errors)
        return data


class DecreaseShelfObjectSerializer(serializers.Serializer):
    amount = serializers.FloatField(min_value=settings.DEFAULT_MIN_QUANTITY)
    description = serializers.CharField(required=False, allow_blank=True)
    shelf_object = serializers.PrimaryKeyRelatedField(
        queryset=ShelfObject.objects.using(settings.READONLY_DATABASE))

    def validate_shelf_object(self, value):
        attr = super().validate(value)
        source_laboratory_id = self.context.get("source_laboratory_id")
        if attr.in_where_laboratory_id != source_laboratory_id:
            logger.debug(
                f'DecreaseShelfObjectSerializer --> attr.in_where_laboratory_id ({attr.in_where_laboratory_id}) != '
                f'source_laboratory_id ({source_laboratory_id})')
            raise serializers.ValidationError(
                _("Object does not exist in the laboratory."))
        return attr

    def validate(self, data):
        amount = data['amount']
        shelf_object = data['shelf_object']
        decrease_errors = {}

        if shelf_object.quantity < amount:
            logger.debug(
                f'DecreaseShelfObjectSerializer --> shelf_object.quantity'
                f' ({shelf_object.quantity}) < amount ({amount})')
            decrease_errors.update({'amount': _("Subtract amount cannot be greater than"
                                                " the available shelf's amount.")})

        limit_obj_error = limit_objects_by_shelf(shelf_object.shelf, shelf_object.object)

        if limit_obj_error:
            decrease_errors.update({'shelf_object': limit_obj_error})

        if decrease_errors:
            raise serializers.ValidationError(decrease_errors)

        return data


class ValidateShelfSerializerCreate(serializers.Serializer):
    # TODO - update this serializer to validate that the shelf belongs to the laboratory, maybe inherit from ValidateShelfSerializer?

    OBJTYPE_CHOICES = (
        ("0", 'Reactive'),
        ("1", 'Material'),
        ("2", 'Equipment'))
    shelf = serializers.PrimaryKeyRelatedField(many=False, queryset=Shelf.objects.using(
        settings.READONLY_DATABASE))
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
    expiration_date = DateFieldWithEmptyString(
        input_formats=settings.DATE_INPUT_FORMATS, required=False,
        allow_null=True)

    class Meta:
        model = ShelfObjectLimits
        fields = '__all__'

    def validate(self, data):
        quantity= self.context.get('quantity',0)
        type_id = self.context.get('type_id','-1')
        without_limit = self.context.get('without_limit',False)
        errors = {}

        if type_id==Object.REACTIVE and not without_limit:
            if data["minimum_limit"] > data["maximum_limit"]:
                logger.debug(
                    f'ShelfObjectLimitsSerializer --> data["minimum_limit"] ({data["minimum_limit"]}) > '
                    f'data["maximum_limit"] ({data["maximum_limit"]})')
                errors.update({"minimum_limit":
                                   _("Minimum limit cannot be greater than maximum limit.")})

            if float(quantity) > data["maximum_limit"]:
                logger.debug(
                    f'ShelfObjectLimitsSerializer --> shelfobject.quantity ({quantity}) > '
                    f'({data["maximum_limit"]})')
                errors.update({"quantity": _(
                    "Quantity cannot be greater than maximum limit.")})

        if errors:
            raise serializers.ValidationError(errors)

        return data


class ReactiveShelfObjectSerializer(ContainerSerializer, serializers.ModelSerializer):
    object = serializers.PrimaryKeyRelatedField(many=False,
                                                queryset=Object.objects.using(
                                                    settings.READONLY_DATABASE),
                                                required=True)
    quantity = serializers.FloatField(required=True)
    measurement_unit = serializers.PrimaryKeyRelatedField(many=False,
                                                          queryset=Catalog.objects.using(
                                                              settings.READONLY_DATABASE),
                                                          required=True)
    marked_as_discard = serializers.BooleanField(default=False, required=False)
    description = serializers.CharField(required=False)
    batch = serializers.CharField(required=True)


    class Meta:
        model = ShelfObject
        fields = ['object', 'shelf', "status", 'quantity', 'measurement_unit',
                  "container_for_cloning", "container_select_option",
                  "available_container", 'limit_quantity', "description",
                  'marked_as_discard', 'batch']

    def validate(self, data):
        data = super().validate(data)
        container = get_selected_container(data)
        errors = validate_measurement_unit_and_quantity(data['shelf'],
                                                        data['object'],
                                                        data['quantity'],
                                                        measurement_unit=data['measurement_unit'],
                                                        container=container)
        if errors:
            raise serializers.ValidationError(errors)
        return data

class ReactiveRefuseShelfObjectSerializer(ContainerSerializer, serializers.ModelSerializer):
    object = serializers.PrimaryKeyRelatedField(many=False,
                                                queryset=Object.objects.using(
                                                    settings.READONLY_DATABASE))
    status = serializers.PrimaryKeyRelatedField(many=False,
                                                queryset=Catalog.objects.using(
                                                    settings.READONLY_DATABASE),
                                                required=True)
    quantity = serializers.FloatField(required=True)
    measurement_unit = serializers.PrimaryKeyRelatedField(many=False,
                                                          queryset=Catalog.objects.using(
                                                              settings.READONLY_DATABASE),
                                                          required=True)
    marked_as_discard = serializers.BooleanField(default=True, required=False)
    description = serializers.CharField(required=False)
    batch = serializers.CharField(required=True)

    class Meta:
        model = ShelfObject
        fields = ["object", "shelf", "status", "quantity","container_for_cloning","container_select_option",
                  "available_container","measurement_unit", "marked_as_discard", "description", 'batch']

    def validate(self, data):
        data = super().validate(data)
        container = get_selected_container(data)
        errors = validate_measurement_unit_and_quantity(data['shelf'],
                                                        data['object'],
                                                        data['quantity'],
                                                        measurement_unit=data['measurement_unit'],
                                                        container=container)
        if errors:
            raise serializers.ValidationError(errors)
        return data

class MaterialShelfObjectSerializer(ValidateShelfSerializer, serializers.ModelSerializer):
    # it inherits the shelf field and its validation from the parent serializer

    object = serializers.PrimaryKeyRelatedField(many=False,
                                                queryset=Object.objects.using(
                                                    settings.READONLY_DATABASE))
    status = serializers.PrimaryKeyRelatedField(many=False,
                                                queryset=Catalog.objects.using(
                                                    settings.READONLY_DATABASE),
                                                required=True)
    quantity = serializers.FloatField(required=True)
    limit_quantity = serializers.FloatField(required=True)
    marked_as_discard = serializers.BooleanField(default=False, required=False)
    description = serializers.CharField(required=False)

    class Meta:
        model = ShelfObject
        fields = ["object", "shelf", "status", "quantity", "limit_quantity",
                  "marked_as_discard",
                  "description"]

    def validate(self, data):
        data = super().validate(data)
        errors = validate_measurement_unit_and_quantity(data['shelf'],
                                                        data['object'],
                                                        data['quantity'])
        if errors:
            raise serializers.ValidationError(errors)
        return data


class MaterialRefuseShelfObjectSerializer(ValidateShelfSerializer, serializers.ModelSerializer):
    # it inherits the shelf field and its validation from the parent serializer

    object = serializers.PrimaryKeyRelatedField(many=False,
                                                queryset=Object.objects.using(
                                                    settings.READONLY_DATABASE))
    status = serializers.PrimaryKeyRelatedField(many=False,
                                                queryset=Catalog.objects.using(
                                                    settings.READONLY_DATABASE),
                                                required=True)
    quantity = serializers.FloatField(required=True)
    limit_quantity = serializers.FloatField(required=True)
    marked_as_discard = serializers.BooleanField(default=True, required=False)
    description = serializers.CharField(required=False)

    class Meta:
        model = ShelfObject
        fields = ["object", "shelf", "status", "quantity", "limit_quantity",
                  "marked_as_discard",
                  "description"]

    def validate(self, data):
        data = super().validate(data)
        errors = validate_measurement_unit_and_quantity(data['shelf'],
                                                        data['object'],
                                                        data['quantity'])
        if errors:
            raise serializers.ValidationError(errors)
        return data


class EquipmentShelfObjectSerializer(ValidateShelfSerializer, serializers.ModelSerializer):
    # it inherits the shelf field and its validation from the parent serializer

    object = serializers.PrimaryKeyRelatedField(many=False,
                                                queryset=Object.objects.using(
                                                    settings.READONLY_DATABASE))
    status = serializers.PrimaryKeyRelatedField(many=False,
                                                queryset=Catalog.objects.using(
                                                    settings.READONLY_DATABASE),
                                                required=True)
    quantity = serializers.FloatField(required=True)
    limit_quantity = serializers.FloatField(required=True)
    marked_as_discard = serializers.BooleanField(default=False, required=False)
    description = serializers.CharField(required=False)

    class Meta:
        model = ShelfObject
        fields = ["object", "shelf", "status", "quantity", "limit_quantity",
                  "marked_as_discard",
                  "description"]

    def validate(self, data):
        data = super().validate(data)
        errors = validate_measurement_unit_and_quantity(data['shelf'],
                                                        data['object'],
                                                        data['quantity'])
        if errors:
            raise serializers.ValidationError(errors)
        return data


class EquipmentRefuseShelfObjectSerializer(ValidateShelfSerializer, serializers.ModelSerializer):
    # it inherits the shelf field and its validation from the parent serializer

    object = serializers.PrimaryKeyRelatedField(many=False,
                                                queryset=Object.objects.using(
                                                    settings.READONLY_DATABASE))
    status = serializers.PrimaryKeyRelatedField(many=False,
                                                queryset=Catalog.objects.using(
                                                    settings.READONLY_DATABASE),
                                                required=True)
    quantity = serializers.FloatField(required=True)
    limit_quantity = serializers.FloatField(required=True)
    marked_as_discard = serializers.BooleanField(default=True, required=False)
    description = serializers.CharField(required=False)

    class Meta:
        model = ShelfObject
        fields = ["object", "shelf", "status", "quantity", "limit_quantity",
                  "marked_as_discard",
                  "description"]

    def validate(self, data):
        data = super().validate(data)
        errors = validate_measurement_unit_and_quantity(data['shelf'],
                                                        data['object'],
                                                        data['quantity'])
        if errors:
            raise serializers.ValidationError(errors)
        return data


class TransferOutShelfObjectSerializer(serializers.Serializer):
    shelf_object = serializers.PrimaryKeyRelatedField(
        queryset=ShelfObject.objects.using(settings.READONLY_DATABASE))
    amount_to_transfer = serializers.FloatField(min_value=settings.DEFAULT_MIN_QUANTITY)
    mark_as_discard = serializers.BooleanField(default=False)
    laboratory = serializers.PrimaryKeyRelatedField(
        queryset=Laboratory.objects.using(settings.READONLY_DATABASE))

    def validate_shelf_object(self, value):
        attr = super().validate(value)
        source_laboratory_id = self.context.get("source_laboratory_id")
        if attr.in_where_laboratory_id != source_laboratory_id:
            logger.debug(
                f'TransferOutShelfObjectSerializer --> attr.in_where_laboratory_id ({attr.in_where_laboratory_id}) != '
                f'source_laboratory_id ({source_laboratory_id})')
            raise serializers.ValidationError(
                _("Object does not exist in the laboratory."))
        return attr


class ShelfObjectDeleteSerializer(serializers.Serializer):
    shelfobj = serializers.PrimaryKeyRelatedField(
        queryset=ShelfObject.objects.using(settings.READONLY_DATABASE))
    delete_container = serializers.BooleanField(default=False, required=False,
                                                allow_null=True)

    def validate_shelfobj(self, value):
        attr = super().validate(value)
        if attr.in_where_laboratory_id != self.context.get('laboratory_id'):
            logger.debug(
                f'ShelfObjectDeleteSerializer --> attr.in_where_laboratory_id ({attr.in_where_laboratory_id}) != '
                f'laboratory_id ({self.context.get("laboratory_id")})')
            raise serializers.ValidationError(
                _("Object does not exist in the laboratory."))
        return attr


class CatalogDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Catalog
        fields = ['description']


class SubstanceCharacteristicsDetailSerializer(serializers.ModelSerializer):
    iarc = CatalogDetailSerializer()
    imdg = CatalogDetailSerializer()
    precursor_type = CatalogDetailSerializer()
    white_organ = CatalogDetailSerializer(many=True)
    storage_class = CatalogDetailSerializer(many=True)
    ue_code = CatalogDetailSerializer(many=True)
    nfpa = CatalogDetailSerializer(many=True)

    class Meta:
        model = SustanceCharacteristics
        fields = '__all__'


class ShelfObjectDetailSerializer(BaseShelfObjectSerializer,
                                  serializers.ModelSerializer):
    object_detail = serializers.SerializerMethodField()
    object_name = serializers.SerializerMethodField()
    unit = serializers.SerializerMethodField()
    object_inst = serializers.SerializerMethodField()
    object_features = serializers.SerializerMethodField(required=False, allow_null=True)
    substance_characteristics = serializers.SerializerMethodField(required=False,
                                                                  allow_null=True)

    class Meta:
        model = ShelfObject
        fields = '__all__'

    def get_substance_characteristics(self, obj):
        if hasattr(obj.object, 'sustancecharacteristics'):
            characteristics = SubstanceCharacteristicsDetailSerializer(
                obj.object.sustancecharacteristics)
            return characteristics.data

    def get_object_detail(self, obj):
        return obj.get_object_detail()

    def get_object_features(self, obj):
        if obj.object.features.exists():
            return list(obj.object.features.all().values('name'))

    def get_object_inst(self, obj):
        object_d = model_to_dict(obj.object)
        del object_d['features']
        return object_d


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
        if quantity == -1 or obj.infinity_quantity:
            quantity = _("Infinity")
        elif quantity:
            quantity = round(quantity, 3)
        return quantity

    def get_measurement_unit(self, obj):
        return obj.get_measurement_unit_display()

    def get_quantity_storage_status(self, obj):
        quantity = obj.quantity
        if obj.infinity_quantity:
            quantity = _("Infinity")
        elif quantity:
            quantity = round(quantity, 3)

        if obj.measurement_unit:
            total = obj.get_total_refuse(include_containers=False,
                                         measurement_unit=obj.measurement_unit)
        else:
            total_detail = ""
            measurement_unit_list = list(set(obj.get_objects().filter(containershelfobject=None) \
                .values_list('measurement_unit', 'measurement_unit__description')))

            for unit in measurement_unit_list:
                total_detail += "%.2f %s<br>" % (
                    obj.get_total_refuse(include_containers=False,
                                         measurement_unit=unit[0]), unit[1]
                )
            return total_detail

        return f'{round(total, 3)} {_("of")} {quantity}'

    def get_percentage_storage_status(self, obj):
        percentage = ""

        if obj.measurement_unit:
            total = obj.get_refuse_porcentage(include_containers=False,
                                              measurement_unit=obj.measurement_unit)
            percentage = f'{round(total, 2)}% {_("of")} 100%'

        if obj.infinity_quantity or not obj.measurement_unit:
            percentage = "-------"
        return percentage

    def get_shelf_info(self, obj):
        position = self.context['position']
        shelf = {
            'obj': obj,
            'type': self.get_type(obj),
            'quantity': self.get_quantity(obj),
            'discard': obj.discard,
            'measurement_unit': self.get_measurement_unit(obj),
            'quantity_storage_status': self.get_quantity_storage_status(obj),
            'percentage_storage_status': self.get_percentage_storage_status(obj),
            'position': position if position in ['bottom', 'left', 'right'] else 'top'
        }
        return render_to_string(
            'laboratory/shelfobject/shelf_availability_information.html',
            context={'shelf': shelf}
        )

    class Meta:
        model = Shelf
        fields = ['name', 'type', 'quantity', 'discard', 'measurement_unit',
                  'quantity_storage_status', 'shelf_info',
                  'percentage_storage_status']


class ShelfObjectStatusSerializer(serializers.Serializer):
    description = serializers.CharField(allow_blank=False, required=True)


class TransferObjectSerializer(serializers.ModelSerializer):
    object = serializers.SerializerMethodField()
    laboratory_send = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()

    def get_object(self, obj):
        return {"name": obj.object.object.name, "type": obj.object.object.type}

    def get_laboratory_send(self, obj):
        return obj.laboratory_send.name

    def get_quantity(self, obj):
        return f"{obj.quantity} {obj.object.get_measurement_unit_display()}"

    class Meta:
        model = TranferObject
        fields = (
            "id", "object", "quantity", "laboratory_send", "update_time",
            "mark_as_discard")


class TransferObjectDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=TransferObjectSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class ShelfObjectObservationSerializer(serializers.ModelSerializer):
    creator_name = serializers.SerializerMethodField()

    class Meta:
        model = ShelfObjectObservation
        fields = ['id', 'action_taken', 'description', 'creator_name', 'creation_date']

    def get_creator_name(self, obj):
        if obj.created_by:
            name = obj.created_by.get_full_name()
            if name:
                return name
            else:
                return obj.created_by.username
        return "No creator"


class ShelfObjectObservationDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ShelfObjectObservationSerializer(),
                                 required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class UpdateShelfObjectStatusSerializer(serializers.Serializer):
    shelf_object = serializers.PrimaryKeyRelatedField(many=False,
                                                      queryset=ShelfObject.objects.using(
                                                          settings.READONLY_DATABASE),
                                                      required=True)
    status = serializers.PrimaryKeyRelatedField(many=False,
                                                queryset=Catalog.objects.filter(
                                                    key='shelfobject_status'),
                                                required=True)
    description = serializers.CharField(required=True)

    def validate_shelf_object(self, value):
        attr = super().validate(value)
        if attr.in_where_laboratory_id != self.context.get('laboratory_id'):
            logger.debug(
                f'UpdateShelfObjectStatusSerializer --> attr.in_where_laboratory_id ({attr.in_where_laboratory_id}) != '
                f'laboratory_id ({self.context.get("laboratory_id")})')
            raise serializers.ValidationError(
                _("Object does not exist in the laboratory."))
        return attr


class MoveShelfObjectSerializer(ValidateShelfSerializer):
    # it inherits the shelf field and its validation from the parent serializer

    lab_room = serializers.PrimaryKeyRelatedField(
        queryset=LaboratoryRoom.objects.using(settings.READONLY_DATABASE))
    furniture = serializers.PrimaryKeyRelatedField(
        queryset=Furniture.objects.using(settings.READONLY_DATABASE))
    shelf_object = serializers.PrimaryKeyRelatedField(
        queryset=ShelfObject.objects.using(settings.READONLY_DATABASE))

    def validate_lab_room(self, value):
        attr = super().validate(value)
        source_laboratory_id = self.context.get("laboratory_id")
        if attr:
            if attr.laboratory_id != source_laboratory_id:
                logger.debug(
                    f'MoveShelfObjectSerializer --> attr.laboratory_id ({attr.laboratory_id}) != '
                    f'source_laboratory_id ({source_laboratory_id})')
                raise serializers.ValidationError(
                    _("Laboratory room does not exist in the laboratory."))
        return attr

    def validate_furniture(self, value):
        attr = super().validate(value)
        source_laboratory_id = self.context.get("laboratory_id")
        if attr:
            if attr.labroom.laboratory_id != source_laboratory_id:
                logger.debug(
                    f'MoveShelfObjectSerializer --> attr.labroom.laboratory_id ({attr.labroom.laboratory_id}) != '
                    f'source_laboratory_id ({source_laboratory_id})')
                raise serializers.ValidationError(
                    _("Furniture does not exist in the laboratory."))
        return attr

    def validate_shelf_object(self, value):
        attr = super().validate(value)
        source_laboratory_id = self.context.get("laboratory_id")
        if attr.in_where_laboratory_id != source_laboratory_id:
            logger.debug(
                f'MoveShelfObjectSerializer --> attr.in_where_laboratory_id ({attr.in_where_laboratory_id}) != '
                f'source_laboratory_id ({source_laboratory_id})')
            raise serializers.ValidationError(
                _("Object does not exist in the laboratory."))
        return attr

    def validate_lab_room_errors(self, laboratory, lab_room, shelf_object):
        lab_room_errors = []
        queryset = LaboratoryRoom.objects.filter(laboratory=laboratory)
        allowed_lab_rooms = get_lab_room_queryset_by_filters(queryset, shelf_object, "furniture__shelf",
                                                        {"furniture__shelf__measurement_unit":
                                                             shelf_object.measurement_unit})
        if lab_room not in allowed_lab_rooms:
            logger.debug(
                f'MoveShelfObjectSerializer --> laboratory room ({lab_room.pk}) is not in available laboratory rooms list')
            lab_room_errors.append(_("Laboratory room is not in available laboratory rooms list."))
        return lab_room_errors

    def validate_furniture_errors(self, lab_room, furniture, shelf_object):
        furniture_errors = []
        queryset = Furniture.objects.filter(labroom=lab_room)
        allowed_furnitures = get_furniture_queryset_by_filters(queryset, shelf_object, "shelf",
                                                        {"shelf__measurement_unit":
                                                             shelf_object.measurement_unit})
        if furniture not in allowed_furnitures:
            logger.debug(
                f'MoveShelfObjectSerializer --> furniture ({furniture.pk}) is not in available furnitures list')
            furniture_errors.append(_("Furniture is not in available furnitures list."))
        return furniture_errors

    def validate_shelf_errors(self, furniture, shelf, shelf_object):
        shelf_errors = []
        queryset = Shelf.objects.filter(furniture=furniture)
        allowed_shelves = get_shelf_queryset_by_filters(queryset, shelf_object, "pk",
                                                        {"measurement_unit":
                                                             shelf_object.measurement_unit})
        if shelf not in allowed_shelves:
            logger.debug(
                f'MoveShelfObjectSerializer --> shelf ({shelf.pk}) is not in available shelves list')
            shelf_errors.append(_("Shelf is not in available shelves list."))
        return shelf_errors

    def validate(self, data):
        data = super().validate(data)
        laboratory = self.context.get("laboratory_id")
        shelf_object = data['shelf_object']
        shelf = data['shelf']
        lab_room = data['lab_room']
        furniture = data['furniture']
        updated_errors = {}
        shelfobject_errors = []
        container = get_selected_container(data)
        measurement_unit = shelf_object.measurement_unit if shelf_object.object.type ==\
                                                            Object.REACTIVE else None
        lab_room_errors = self.validate_lab_room_errors(laboratory, lab_room, shelf_object)
        furniture_errors = self.validate_furniture_errors(lab_room, furniture, shelf_object)
        shelf_errors = self.validate_shelf_errors(furniture, shelf, shelf_object)

        if shelf.pk == shelf_object.shelf.pk:
            logger.debug(f'MoveShelfObjectSerializer --> shelf ({shelf.pk}) == shelf_object.shelf.pk ({shelf_object.shelf.pk})')
            raise serializers.ValidationError({'shelf': _("Object cannot be moved to same shelf.")})

        errors = validate_measurement_unit_and_quantity(shelf,
                                                        shelf_object.object,
                                                        shelf_object.quantity,
                                                        measurement_unit=measurement_unit,
                                                        container=container)
        if errors or shelf_errors or lab_room_errors or furniture_errors:

            updated_errors = group_object_errors_for_serializer(errors)

            if shelf_errors:
                updated_errors['shelf'] = shelf_errors
            if lab_room_errors:
                updated_errors['lab_room'] = lab_room_errors
            if furniture_errors:
                updated_errors['furniture'] = furniture_errors
            raise serializers.ValidationError(updated_errors)
        return data


class ValidateUserAccessShelfSerializer(ValidateUserAccessOrgLabSerializer):
    shelf = serializers.PrimaryKeyRelatedField(
        queryset=Shelf.objects.using(settings.READONLY_DATABASE))


class ValidateUserAccessShelfTypeSerializer(ValidateUserAccessOrgLabSerializer):
    OBJTYPE_CHOICES = (
        ("0", 'Reactive'),
        ("1", 'Material'),
        ("2", 'Equipment'))
    shelf = serializers.PrimaryKeyRelatedField(many=False, queryset=Shelf.objects.using(
        settings.READONLY_DATABASE), required=True)
    objecttype = serializers.ChoiceField(choices=OBJTYPE_CHOICES, required=True)


class TransferInShelfObjectSerializer(ValidateShelfSerializer):
    # it inherits the shelf field and its validation from the parent serializer

    transfer_object = serializers.PrimaryKeyRelatedField(
        queryset=TranferObject.objects.using(settings.READONLY_DATABASE).filter(
            status=REQUESTED))

    def validate_transfer_object(self, value):
        attr = super().validate(value)
        if attr.laboratory_received_id != self.context.get('laboratory_id'):
            logger.debug(
                f'TransferInShelfObjectSerializer --> attr.laboratory_received ({attr.laboratory_received}) != '
                f'laboratory_id ({self.context.get("laboratory_id")})')
            raise serializers.ValidationError(
                _("Transfer was not sent to the laboratory."))
        if self.context.get(
            'validate_for_approval'):  # validations specific for transfer in approve, ignored for deny
            if attr.object.in_where_laboratory != attr.laboratory_send:
                logger.debug(
                    f'TransferInShelfObjectSerializer --> attr.object.in_where_laboratory ({attr.object.in_where_laboratory}) != '
                    f'attr.laboratory_send ({attr.laboratory_send})')
                raise serializers.ValidationError(
                    _("The transfer in cannot be performed since the source object no longer belongs to the laboratory that sent it."))
            if attr.quantity > attr.object.quantity:
                logger.debug(
                    f'TransferInShelfObjectSerializer --> attr.quantity ({attr.quantity}) > '
                    f'attr.object.quantity ({attr.object.quantity})')
                raise serializers.ValidationError(
                    _("The transfer in cannot be performed since the transfer quantity is bigger than the quantity available in the " \
                      "source object."))
        return attr

    def validate(self, data):
        data = super().validate(data)
        if self.context.get('validate_for_approval'):
            transfer_object = data['transfer_object']
            # do it here instead of in validate_transfer_object so shelf is already validated when used - only validate measurement unit for reactive
            measurement_unit = transfer_object.object.measurement_unit if transfer_object.object.object.type == Object.REACTIVE else None
            container = get_selected_container(data)
            errors = validate_measurement_unit_and_quantity(data['shelf'],
                                                            transfer_object.object.object,
                                                            transfer_object.quantity,
                                                            measurement_unit=measurement_unit,
                                                            container=container)
            if errors:
                updated_errors = group_object_errors_for_serializer(errors, save_to_key="transfer_object")
                raise serializers.ValidationError(updated_errors)
        return data


class ShelfObjectPk(serializers.Serializer):
    search = serializers.CharField(min_length=4)

    def validate_search(self, value):
        attr = super().validate(value)
        if not re.findall('pk?=?(\d+)', attr):
            raise serializers.ValidationError(_("Invalid search"))
        return attr


class SearchShelfObjectSerializer(serializers.Serializer):
    labroom = serializers.PrimaryKeyRelatedField(
        queryset=LaboratoryRoom.objects.using(settings.READONLY_DATABASE),
        allow_null=True, allow_empty=True, required=False)
    furniture = serializers.PrimaryKeyRelatedField(
        queryset=Furniture.objects.using(settings.READONLY_DATABASE),
        allow_null=True, allow_empty=True, required=False)
    shelf = serializers.PrimaryKeyRelatedField(
        queryset=Shelf.objects.using(settings.READONLY_DATABASE),
        allow_null=True, allow_empty=True, required=False)
    shelfobject = serializers.PrimaryKeyRelatedField(
        queryset=ShelfObject.objects.filter(containershelfobject=None).using(
            settings.READONLY_DATABASE),
        allow_null=True, allow_empty=True, required=False)

    def validate_laboratory(self, lab_pk, obj_name):
        source_laboratory_id = self.context.get("source_laboratory_id")
        if lab_pk != source_laboratory_id:
            raise serializers.ValidationError(
                _("%s does not exist in the laboratory.") % (obj_name))

    def validate_labroom_data(self, data):
        if 'labroom' in data:
            self.validate_laboratory(data['labroom'].laboratory_id, "Laboratory room")

    def validate_furniture_data(self, data):
        if 'furniture' in data:
            self.validate_laboratory(data['furniture'].labroom.laboratory_id,
                                     "Furniture")

            if 'labroom' in data and data['furniture'].labroom.pk != data['labroom'].pk:
                raise serializers.ValidationError({'furniture': _(
                    "Furniture does not exist in the laboratory room.")})

    def validate_shelf_data(self, data):
        if 'shelf' in data:
            self.validate_laboratory(data['shelf'].furniture.labroom.laboratory_id,
                                     "Shelf")

            if 'furniture' in data and data['shelf'].furniture.pk != data[
                'furniture'].pk:
                raise serializers.ValidationError(
                    {'shelf': _("Shelf does not exist in the furniture.")})

            if 'labroom' in data and data['labroom'].pk != data[
                'shelf'].furniture.labroom.pk:
                raise serializers.ValidationError(
                    {'shelfobject': _("Shelf does not exist in the labroom.")})

    def validate_shelfobject_data(self, data):
        if 'shelfobject' in data:
            self.validate_laboratory(data['shelfobject'].in_where_laboratory_id,
                                     "Object")

            if 'shelf' in data and data['shelfobject'].shelf.pk != data['shelf'].pk:
                raise serializers.ValidationError(
                    {'shelfobject': _("Object does not exist in the shelf.")})

            if 'furniture' in data and data['furniture'].pk != data[
                'shelfobject'].shelf.furniture.pk:
                raise serializers.ValidationError(
                    {'shelfobject': _("Object does not exist in the furniture.")})

            if 'labroom' in data and data['labroom'].pk != data[
                'shelfobject'].shelf.furniture.labroom.pk:
                raise serializers.ValidationError(
                    {'shelfobject': _("Object does not exist in the labroom.")})

    def validate(self, data):
        self.validate_labroom_data(data)
        self.validate_furniture_data(data)
        self.validate_shelf_data(data)
        self.validate_shelfobject_data(data)
        return data


class SearchShelfObjectSerializerMany(serializers.Serializer):
    labroom = serializers.PrimaryKeyRelatedField(
        queryset=LaboratoryRoom.objects.using(settings.READONLY_DATABASE),
        allow_null=True, allow_empty=True, required=False, many=True)
    furniture = serializers.PrimaryKeyRelatedField(
        queryset=Furniture.objects.using(settings.READONLY_DATABASE),
        allow_null=True, allow_empty=True, required=False, many=True)
    shelf = serializers.PrimaryKeyRelatedField(
        queryset=Shelf.objects.using(settings.READONLY_DATABASE),
        allow_null=True, allow_empty=True, required=False, many=True)
    shelfobject = serializers.PrimaryKeyRelatedField(
        queryset=ShelfObject.objects.filter(containershelfobject=None).using(
            settings.READONLY_DATABASE),
        allow_null=True, allow_empty=True, required=False, many=True)

    object = serializers.PrimaryKeyRelatedField(
        queryset=Object.objects.using(settings.READONLY_DATABASE), allow_null=True,
        allow_empty=True, required=False, many=True)

    def validate_laboratory(self, lab_pk, obj_name):
        source_laboratory_id = self.context.get("source_laboratory_id")
        if lab_pk != source_laboratory_id:
            raise serializers.ValidationError(
                _("%s does not exist in the laboratory.") % (obj_name))

    def validate_labroom_data(self, data):
        if 'labroom' in data:
            for labroom in data['labroom']:
                self.validate_laboratory(labroom.laboratory_id, "Laboratory room")

    def validate_furniture_data(self, data):
        if 'furniture' in data:
            for furniture in data['furniture']:
                self.validate_laboratory(furniture.labroom.laboratory_id, "Furniture")

    def validate_shelf_data(self, data):
        if 'shelf' in data:
            for shelf in data['shelf']:
                self.validate_laboratory(shelf.furniture.labroom.laboratory_id, "Shelf")

    def validate_shelfobject_data(self, data):
        if 'shelfobject' in data:
            for shelfobject in data['shelfobject']:
                self.validate_laboratory(shelfobject.in_where_laboratory_id,
                                         "ShelfObject")

    def validate_object_data(self, data):
        if 'object' in data:
            for object in data['object']:
                lab_pk = self.context.get("source_laboratory_id")
                shelf_object = ShelfObject.objects.filter(object=object,
                                                          in_where_laboratory=lab_pk)
                if not shelf_object.exists():
                    raise serializers.ValidationError(
                        _("Object does not exist in the laboratory."))

    def validate(self, data):
        self.validate_labroom_data(data)
        self.validate_furniture_data(data)
        self.validate_shelf_data(data)
        self.validate_shelfobject_data(data)
        self.validate_object_data(data)
        return data


class TransferInShelfObjectApproveWithContainerSerializer(TransferInShelfObjectSerializer, ContainerSerializer):
    TRANSFER_IN_CONTAINER_SELECT_CHOICES = [
        ('clone', _('Create new based on selected')),
        ('available', _('Use selected')),
        ('use_source', _('Move the container from the source laboratory')),
        ('new_based_source',
         _('Create new based on current container in the source laboratory'))
    ]
    container_select_option = serializers.ChoiceField(required=True,
                                                      choices=TRANSFER_IN_CONTAINER_SELECT_CHOICES)

    def validate(self, data):
        data = super().validate(data)
        container_select_option = data['container_select_option']
        transfer_object = data['transfer_object']
        if container_select_option in (
        "use_source", "new_based_source") and not transfer_object.object.container:
            logger.debug(
                f'TransferInShelfObjectApproveWithContainerSerializer --> container_select_option in ("use_source", "new_based_source") '
                f'and not transfer_object.object.container')
            raise serializers.ValidationError({'container_select_option':
                                                   _("The selected option cannot be used since the source object does not have a container assigned.")})
        if container_select_option == "use_source" and transfer_object.quantity < transfer_object.object.quantity:
            logger.debug(
                f'TransferInShelfObjectApproveWithContainerSerializer --> container_select_option == "use_source" and '
                f'transfer_object.quantity ({transfer_object.quantity}) < transfer_object.object.quantity ({transfer_object.object.quantity})')
            raise serializers.ValidationError({"container_select_option":
                                                   _("The source container cannot be moved since the entire quantity available for the source object was not transferred in.")})
        return data


class MoveShelfObjectWithContainerSerializer(MoveShelfObjectSerializer, ContainerSerializer):
    MOVE_CONTAINER_SELECT_CHOICES = [
        ('clone', _('Create new based on selected')),
        ('available', _('Use selected')),
        ('use_source', _('Move the container from the source laboratory')),
        ('new_based_source', _('Create new based on current container in the source laboratory'))
    ]
    container_select_option = serializers.ChoiceField(required=True, choices=MOVE_CONTAINER_SELECT_CHOICES)

    def validate(self, data):
        data = super().validate(data)
        container_select_option = data['container_select_option']
        shelf_object = data['shelf_object']
        if container_select_option in ("use_source", "new_based_source") and not shelf_object.container:
            logger.debug(f'MoveShelfObjectWithContainerSerializer --> container_select_option in ("use_source", "new_based_source") '
                         f'and not shelf_object.container')
            raise serializers.ValidationError({'container_select_option':
                _("The selected option cannot be used since the source object does not have a container assigned.")})
        return data


class ManageContainerSerializer(ContainerSerializer):
    shelf_object = serializers.PrimaryKeyRelatedField(queryset=ShelfObject.objects.using(settings.READONLY_DATABASE))

    def validate(self, data):
        data = super().validate(data)
        shelf_object = data['shelf_object']
        container = get_selected_container(data)
        errors = validate_measurement_unit_and_quantity(data['shelf'],
                                                        shelf_object.object,
                                                        shelf_object.quantity,
                                                        measurement_unit=shelf_object.measurement_unit,
                                                        container=container)
        if errors:
            updated_errors = group_object_errors_for_serializer(errors)
            raise serializers.ValidationError(updated_errors)
        return data


class ValidateShelfInformationPositionSerializer(ValidateShelfSerializer):
    # it inherits the shelf field and its validation from the parent serializer

    position = serializers.CharField(allow_null=True, allow_blank=True, required=False)


class ProviderDisplayNameSerializer(GTS2SerializerBase):
    display_fields = 'name'

class CreateMaintenanceSerializer(serializers.ModelSerializer):
    maintenance_date = DateFieldWithEmptyString(
        input_formats=settings.DATE_INPUT_FORMATS, required=False,
        allow_null=True)
    provider_of_maintenance = serializers.PrimaryKeyRelatedField(queryset=Provider.objects.using(settings.READONLY_DATABASE))
    maintenance_observation = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.using(settings.READONLY_DATABASE))
    validator = serializers.PrimaryKeyRelatedField(queryset=Profile.objects.using(settings.READONLY_DATABASE))
    organization = serializers.PrimaryKeyRelatedField(queryset=OrganizationStructure.objects.using(settings.READONLY_DATABASE))

    class Meta:
        model = ShelfObjectMaintenance
        fields = "__all__"

class UpdateMaintenanceSerializer(serializers.ModelSerializer):
    maintenance_date = DateFieldWithEmptyString(
        input_formats=settings.DATE_INPUT_FORMATS, required=True,
        allow_null=True)
    provider_of_maintenance = serializers.PrimaryKeyRelatedField(queryset=Provider.objects.using(settings.READONLY_DATABASE))
    maintenance_observation = serializers.CharField(allow_null=True, allow_blank=True, required=False)

    class Meta:
        model = ShelfObjectMaintenance
        fields = ["maintenance_date","provider_of_maintenance","maintenance_observation"]

class MaintenanceSerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    provider_of_maintenance = ProviderDisplayNameSerializer(many=False)

    def get_actions(self, obj):
        user = self.context["request"].user
        action_list = {
            "create": ["laboratory.add_shelfobjectmaintenance",
                       "laboratory.view_shelfobjectmaintenance"],
            "update": ["laboratory.change_shelfobjectmaintenance",
                       "laboratory.view_shelfobjectmaintenance"],
            "destroy": ["laboratory.delete_shelfobjectmaintenance",
                        "laboratory.view_shelfobjectmaintenance"],
            "detail": ["laboratory.view_shelfobjectmaintenance"]
        }
        return get_actions_by_perms(user, action_list)

    class Meta:
        model = ShelfObjectMaintenance
        fields = ['id', 'maintenance_date', 'provider_of_maintenance', 'validator',
                  'maintenance_observation', 'actions']


class MaintenanceDatatableSerializer(serializers.Serializer):
    data = serializers.ListField(child=MaintenanceSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)

class ValidateShelfObjectLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShelfObjectLog
        fields = ["id","shelfobject","description"]

class ShelfObjectLogSerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()

    def get_actions(self, obj):
        user = self.context["request"].user
        action_list = {
            "create": ["laboratory.add_shelfobjectlog",
                       "laboratory.view_shelfobjectlog"],
            "update": ["laboratory.change_shelfobjectlog",
                       "laboratory.view_shelfobjectlog"],
            "destroy": ["laboratory.delete_shelfobjectlog",
                        "laboratory.view_shelfobjectlog"],
            "detail": ["laboratory.view_shelfobjectlog"]
        }
        return get_actions_by_perms(user, action_list)

    class Meta:
        model = ShelfObjectLog
        fields = ['id', 'description','last_update','actions']


class ShelfObjectLogDatatableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ShelfObjectLogSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class ValidateShelfObjectCalibrateSerializer(serializers.ModelSerializer):
    calibration_date = DateFieldWithEmptyString(
        input_formats=settings.DATE_INPUT_FORMATS, required=True,
        allow_null=False)
    calibrate_name = serializers.CharField(max_length=50, required=True, allow_null=False,allow_blank=False)
    observation = serializers.CharField(max_length=500, required=False, allow_null=True,allow_blank=True)
    validator = serializers.PrimaryKeyRelatedField(queryset= Profile.objects.using(settings.READONLY_DATABASE))
    shelfobject = serializers.PrimaryKeyRelatedField(queryset= ShelfObject.objects.using(settings.READONLY_DATABASE))
    organization = serializers.PrimaryKeyRelatedField(queryset= OrganizationStructure.objects.using(settings.READONLY_DATABASE))
    created_by = serializers.PrimaryKeyRelatedField(queryset= User.objects.using(settings.READONLY_DATABASE))

    class Meta:
        model = ShelfObjectCalibrate
        fields = ['id', 'shelfobject','calibration_date','calibrate_name','validator','organization',
                  'created_by','observation']


class UpdateShelfObjectCalibrateSerializer(serializers.ModelSerializer):
    calibration_date = DateFieldWithEmptyString(
        input_formats=settings.DATE_INPUT_FORMATS, required=True,
        allow_null=False)
    calibrate_name = serializers.CharField(max_length=100,required=True, allow_null=False, allow_blank=False)
    observation = serializers.CharField(allow_null=True, allow_blank=True, required=False)

    class Meta:
        model = ShelfObjectMaintenance
        fields = ["calibration_date","calibrate_name","observation"]
class ShelfObjectCalibrateSerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    validator = serializers.SerializerMethodField()
    def get_validator(self,obj):
        if obj.validator:
            return obj.validator.__str__()
        return ""

    def get_actions(self, obj):
        user = self.context["request"].user
        action_list = {
            "create": ["laboratory.add_shelfobjectcalibrate",
                       "laboratory.view_shelfobjectcalibrate"],
            "update": ["laboratory.change_shelfobjectcalibrate",
                       "laboratory.view_shelfobjectcalibrate"],
            "destroy": ["laboratory.delete_shelfobjectcalibrate",
                        "laboratory.view_shelfobjectcalibrate"],
            "detail": ["laboratory.view_shelfobjectcalibrate"]
        }
        return get_actions_by_perms(user, action_list)

    class Meta:
        model = ShelfObjectCalibrate
        fields = ['id', 'calibration_date','calibrate_name','validator','observation','actions']


class ShelfObjectCalibrateDatatableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ShelfObjectCalibrateSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class CreateShelfObjectGuaranteeSerializer(serializers.ModelSerializer):
    guarantee_initial_date = DateFieldWithEmptyString(
        input_formats=settings.DATE_INPUT_FORMATS, required=True,
        allow_null=False)
    guarantee_final_date = DateFieldWithEmptyString(
        input_formats=settings.DATE_INPUT_FORMATS, required=True,
        allow_null=False)
    contract = ChunkedFileField(required=False, allow_empty_file=True)
    shelfobject = serializers.PrimaryKeyRelatedField(queryset= ShelfObject.objects.using(settings.READONLY_DATABASE))
    organization = serializers.PrimaryKeyRelatedField(queryset= OrganizationStructure.objects.using(settings.READONLY_DATABASE))
    created_by = serializers.PrimaryKeyRelatedField(queryset= User.objects.using(settings.READONLY_DATABASE))

    class Meta:
        model = ShelfObjectGuarantee
        fields = ["id","shelfobject","guarantee_initial_date", "guarantee_final_date",
                  "contract",'organization','created_by']

    def validate(self, data):
        initial_date = data['guarantee_initial_date']
        final_date = data['guarantee_final_date']
        errors = {}

        if initial_date > final_date:
            errors.update({'guarantee_initial_date': _("Initial date cannot be greater than final date.")})

        if errors:
            raise serializers.ValidationError(errors
                                              )
        return data

class UpdateShelfObjectGuaranteeSerializer(serializers.ModelSerializer):
    guarantee_initial_date = DateFieldWithEmptyString(
        input_formats=settings.DATE_INPUT_FORMATS, required=True,
        allow_null=False)
    guarantee_final_date = DateFieldWithEmptyString(
        input_formats=settings.DATE_INPUT_FORMATS, required=True,
        allow_null=False)

    class Meta:
        model = ShelfObjectGuarantee
        exclude = ['shelfobject','organization','created_by']


    def validate(self, data):
        initial_date = data['guarantee_initial_date']
        final_date = data['guarantee_final_date']
        errors = {}
        print(354135)

        if initial_date > final_date:
            errors.update({'guarantee_initial_date': _("Initial date cannot be greater than final date.")})

        if errors:
            raise serializers.ValidationError(errors)
        return data

class ShelfObjectGuaranteeSerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()

    def get_actions(self, obj):
        user = self.context["request"].user
        action_list = {
            "create": ["laboratory.add_shelfobjectguarantee", "laboratory.view_shelfobjectguarantee"],
            "update": ["laboratory.change_shelfobjectguarantee", "laboratory.view_shelfobjectguarantee"],
            "destroy": ["laboratory.delete_shelfobjectguarantee", "laboratory.view_shelfobjectguarantee"],
            "detail": ["laboratory.view_shelfobjectguarantee"]
        }
        return get_actions_by_perms(user, action_list)

    class Meta:
        model = ShelfObjectGuarantee
        fields = ['id', 'guarantee_initial_date','guarantee_final_date','contract','actions']


class ShelfObjectGuaranteeDatatableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ShelfObjectGuaranteeSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)

class CreateShelfObjectTrainingSerializer(serializers.ModelSerializer):
    training_initial_date = DateFieldWithEmptyString(
        input_formats=settings.DATE_INPUT_FORMATS, required=True,
        allow_null=False)
    training_final_date = DateFieldWithEmptyString(
        input_formats=settings.DATE_INPUT_FORMATS, required=True,
        allow_null=False)
    number_of_hours = serializers.IntegerField(required=True)
    intern_people_receive_training = serializers.PrimaryKeyRelatedField(queryset=Profile.objects.using(settings.READONLY_DATABASE), many=True)
    observation = serializers.CharField(max_length=500, required=False, allow_blank="")
    external_people_receive_training = serializers.CharField(max_length=500, required=False, allow_blank="")
    shelfobject = serializers.PrimaryKeyRelatedField(queryset= ShelfObject.objects.using(settings.READONLY_DATABASE))
    organization = serializers.PrimaryKeyRelatedField(queryset= OrganizationStructure.objects.using(settings.READONLY_DATABASE))
    created_by = serializers.PrimaryKeyRelatedField(queryset= User.objects.using(settings.READONLY_DATABASE))

    class Meta:
        model = ShelfObjectTraining
        fields = ["id","shelfobject","training_initial_date", "training_final_date",
                  "number_of_hours","intern_people_receive_training","observation",
                  "external_people_receive_training",'organization','created_by']

    def validate(self, data):
        initial_date = data['training_initial_date']
        final_date = data['training_final_date']
        errors = {}

        if initial_date > final_date:
            errors.update({'training_initial_date': _("Initial date cannot be greater than final date.")})

        if errors:
            raise serializers.ValidationError(errors
                                              )
        return data
class UpdateShelfObjectTrainingSerializer(serializers.ModelSerializer):
    training_initial_date = DateFieldWithEmptyString(
        input_formats=settings.DATE_INPUT_FORMATS, required=True,
        allow_null=False)
    training_final_date = DateFieldWithEmptyString(
        input_formats=settings.DATE_INPUT_FORMATS, required=True,
        allow_null=False)
    number_of_hours = serializers.IntegerField(required=True)
    intern_people_receive_training = serializers.PrimaryKeyRelatedField(queryset=Profile.objects.using(settings.READONLY_DATABASE), many=True)
    observation = serializers.CharField(max_length=500, required=False, allow_blank="")
    external_people_receive_training = serializers.CharField(max_length=500, required=False, allow_blank="")

    class Meta:
        model = ShelfObjectTraining
        exclude = ['shelfobject','organization','created_by']

    def validate(self, data):
        initial_date = data['training_initial_date']
        final_date = data['training_final_date']
        errors = {}

        if initial_date > final_date:
            errors.update({'training_initial_date': _("Initial date cannot be greater than final date.")})

        if errors:
            raise serializers.ValidationError(errors
                                              )
        return data
class ShelfObjectTrainingSerializer(serializers.ModelSerializer):

    actions = serializers.SerializerMethodField()

    def get_actions(self, obj):
        user = self.context["request"].user
        action_list = {
            "create": ["laboratory.add_shelfobjecttraining",
                       "laboratory.view_shelfobjecttraining"],
            "update": ["laboratory.change_shelfobjecttraining",
                       "laboratory.view_shelfobjecttraining"],
            "destroy": ["laboratory.delete_shelfobjecttraining",
                        "laboratory.view_shelfobjecttraining"],
            "detail": ["laboratory.view_shelfobjecttraining"]
        }
        return get_actions_by_perms(user, action_list)

    class Meta:
        model = ShelfObjectTraining
        fields = ['id', 'training_initial_date','training_final_date','number_of_hours',
                  'intern_people_receive_training','observation','actions',
                  'external_people_receive_training']


class ShelfObjectTrainingeDatatableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ShelfObjectTrainingSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class ShelfObjectLogtFilter(FilterSet):
    class Meta:
        model = ShelfObjectLog
        fields = {'id': ['exact'],
                   'description': ['icontains'],
                   }

class ShelfObjectCalibrateFilter(FilterSet):
    class Meta:
        model = ShelfObjectCalibrate
        fields = {'id': ['exact'],
                   'calibrate_name': ['icontains'],
                   'observation': ['icontains'],
                   }
class ShelfObjectTrainingFilter(FilterSet):
    class Meta:
        model = ShelfObjectTraining
        fields = {'id': ['exact'],
                   'number_of_hours': ['exact'],
                   'observation': ['icontains'],
                   }

class ShelfObjectMaintenanceFilter(FilterSet):
    class Meta:
        model = ShelfObjectMaintenance
        fields = {'id': ['exact'],
                   'provider_of_maintenance__name': ['icontains'],
                   'validator': ['exact'],
                   'maintenance_observation': ['icontains'],
                   }
