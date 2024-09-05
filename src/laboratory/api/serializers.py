import logging

from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from djgentelella.fields.files import ChunkedFileField
from djgentelella.serializers.selects import GTS2SerializerBase
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from auth_and_perms.organization_utils import user_is_allowed_on_organization, \
    organization_can_change_laboratory
from laboratory.models import CommentInform, Inform, ShelfObject, OrganizationStructure, \
    Shelf, Laboratory, \
    ShelfObjectObservation, Object, ObjectFeatures, Provider, Catalog, EquipmentType, \
    EquipmentCharacteristics, MaterialCapacity
from laboratory.models import Protocol
from laboratory.utils import get_actions_by_perms
from organilab.settings import DATETIME_INPUT_FORMATS
from reservations_management.models import ReservedProducts, Reservations

logger = logging.getLogger('organilab')


class ReservedProductsSerializer(serializers.ModelSerializer):
    initial_date = serializers.DateTimeField(input_formats=DATETIME_INPUT_FORMATS)
    final_date = serializers.DateTimeField(input_formats=DATETIME_INPUT_FORMATS)

    class Meta:
        model = ReservedProducts
        fields = '__all__'


class ReservedProductsSerializerUpdate(serializers.ModelSerializer):
    class Meta:
        model = ReservedProducts
        fields = ["reservation", "status"]


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservations
        fields = '__all__'


class CommentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentInform
        fields = '__all__'


class ProtocolSerializer(serializers.ModelSerializer):
    action = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()

    def get_file(self, obj):
        if not obj:
            return {
                'url': '#',
                'display_name': _("File not found")
            }

        return {
            'url': obj.file.url,
            'class': 'btn btn-sm btn-outline-success',
            'display_name': "<i class='fa fa-download' aria-hidden='true'></i> %s" % _(
                "Download")
        }

    def get_action(self, obj):
        user = self.context['request'].user
        org_pk = self.context['request'].GET['org_pk']
        btn = ''
        if user.has_perm('laboratory.change_protocol'):
            btn += "<a href=\"%s\" class='btn btn-outline-warning btn-sm'><i class='fa fa-edit' aria-hidden='true'></i> %s</a>" % (
                reverse('laboratory:protocol_update',
                        args=(org_pk, obj.laboratory.pk, obj.pk)),
                _("Edit")
            )
        if user.has_perm('laboratory.delete_protocol'):
            btn += "<a href=\"%s\" class='btn btn-outline-danger btn-sm'><i class='fa fa-trash' aria-hidden='true'></i> %s</a>" % (
                reverse('laboratory:protocol_delete',
                        args=(org_pk, obj.laboratory.pk, obj.pk)),
                _("Delete")
            )

        return btn

    class Meta:
        model = Protocol
        fields = ['name', 'short_description', 'file', 'action']


class ProtocolDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ProtocolSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class LogEntryUserSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    action_flag = serializers.SerializerMethodField()
    action_time = serializers.DateTimeField(format=DATETIME_INPUT_FORMATS[0])

    def get_user(self, obj):
        if not obj:
            return _("No user found")
        if not obj.user:
            return _("No user found")

        name = obj.user.get_full_name()
        if not name:
            name = obj.username
        return name

    def get_action_flag(self, obj):
        if obj.action_flag in [1, 2]:
            return _("Register") if obj.action_flag == 1 else ("Login")
        return ''

    class Meta:
        model = LogEntry
        fields = '__all__'


class LogEntryUserDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=LogEntryUserSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class LogEntrySerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    action_flag = serializers.SerializerMethodField()
    action_time = serializers.DateTimeField(format=DATETIME_INPUT_FORMATS[0])

    def get_user(self, obj):
        if not obj:
            return _("No user found")
        if not obj.user:
            return _("No user found")

        name = obj.user.get_full_name()
        if not name:
            name = obj.user.username
        return name

    def get_action_flag(self, obj):
        return obj.get_action_flag_display()

    class Meta:
        model = LogEntry
        fields = '__all__'


class LogEntryDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=LogEntrySerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class InformSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    start_application_date = serializers.DateField()
    close_application_date = serializers.DateField()
    action = serializers.SerializerMethodField()

    def get_status(self, obj):
        return obj.get_status_display()

    def get_action(self, obj):
        if obj and self.context['request'].user.has_perm('laboratory.add_inform'):
            return """
                    <a href="%s"><i class="fa fa-eye" aria-hidden="true"></i></a>
                    """ % (
                reverse('laboratory:complete_inform', kwargs={
                    'org_pk': self.context['view'].kwargs['pk'],
                    'lab_pk': obj.object_id,
                    'pk': obj.pk
                })
            )
        return ""

    class Meta:
        model = Inform
        fields = ['name', 'start_application_date', 'close_application_date', 'status',
                  'action']


class InformDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=InformSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class BaseShelfObjectSerializer:

    def get_object_type(self, obj):
        return obj.object.get_type_display()

    def get_object_name(self, obj):
        return obj.object.name

    def get_unit(self, obj):
        return obj.get_measurement_unit_display()

    def get_last_update(self, obj):
        return obj.last_update.date()

    def get_created_by(self, obj):
        if obj.created_by:
            return str(obj.created_by)
        else:
            return _('Unknown')

    def get_container(self, obj):
        if obj.container:
            return obj.container.object.name
        return ''


class ShelfObjectSerialize(BaseShelfObjectSerializer, serializers.ModelSerializer):
    action = serializers.SerializerMethodField()
    object_name = serializers.SerializerMethodField()
    unit = serializers.SerializerMethodField()
    last_update = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    def get_action(self, obj):
        if obj:
            org_pk = self.context['org_pk']
            if obj.created_by:
                return """
                        <a href="%s" class="btn btn-secondary" target="_blank"><i class="fa fa-eye" aria-hidden="true"></i></a>
                        """ % (
                    reverse('laboratory:profile_detail', kwargs={
                        'org_pk': org_pk,
                        'pk': obj.created_by.pk
                    })
                )
            else:
                return ""
        return ""

    class Meta:
        model = ShelfObject
        fields = ['object_name', 'unit', 'quantity', 'last_update', 'created_by',
                  'action']


class ShelfPkList(serializers.Serializer):
    shelfs = serializers.ListField(child=serializers.IntegerField(), allow_null=False,
                                   allow_empty=False)


class ShelfObjectLaboratoryViewSerializer(BaseShelfObjectSerializer,
                                          serializers.ModelSerializer):
    object_type = serializers.SerializerMethodField()
    object_name = serializers.SerializerMethodField()
    unit = serializers.SerializerMethodField()
    last_update = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    container = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    def get_actions(self, obj):
        context = {
            'laboratory': self.context['view'].laboratory,
            'org_pk': self.context['view'].organization,
            'shelfobject': obj
        }
        return render_to_string(
            'laboratory/serializers/shelfobject_actions.html',
            request=self.context['request'],
            context=context
        )

    class Meta:
        model = ShelfObject
        fields = ['pk', 'object_type', 'object_name', 'unit', 'quantity', 'last_update',
                  'created_by', 'container', 'actions']


class ShelfObjectTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ShelfObjectLaboratoryViewSerializer(),
                                 required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class BaseOrganizationLaboratory(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(
        queryset=OrganizationStructure.objects.using(settings.READONLY_DATABASE))
    laboratory = serializers.PrimaryKeyRelatedField(
        queryset=Laboratory.objects.using(settings.READONLY_DATABASE))

    def validate_organization(self, value):
        user_is_allowed_on_organization(self.user, value)
        return value

    def validate(self, value):
        if not organization_can_change_laboratory(value['laboratory'],
                                                  value['organization']):
            raise ValidationError(detail="Wrong Laboratory")
        return value

    user = None

    def set_user(self, user):
        self.user = user


class ShelfLabViewSerializer(serializers.Serializer):
    shelf = serializers.PrimaryKeyRelatedField(
        queryset=Shelf.objects.using(settings.READONLY_DATABASE), required=False)

    def __init__(self, *args, **kwargs):
        self.laboratory = kwargs.pop('laboratory')
        super().__init__(*args, **kwargs)

    def validate(self, value):
        value = super().validate(value)
        if 'shelf' not in value:
            value['shelf'] = None

        if value['shelf'] is not None:
            if self.laboratory != value['shelf'].furniture.labroom.laboratory:
                raise ValidationError(detail="Shelf not found on Laboratory")
        return value


class CreateObservationShelfObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShelfObjectObservation
        fields = ['action_taken', 'description']


class ValidateEquipmentSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=255)
    synonym = serializers.CharField(max_length=255, allow_null=True, allow_blank=True,
                                    required=False)
    description = serializers.CharField(allow_null=True, allow_blank=True,
                                        required=False)
    type = serializers.CharField(max_length=2)
    is_public = serializers.BooleanField(required=False)
    features = serializers.PrimaryKeyRelatedField(many=True,
                                                  queryset=ObjectFeatures.objects.using(
                                                      settings.READONLY_DATABASE),
                                                  required=True, allow_empty=False)
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.using(settings.READONLY_DATABASE), allow_empty=True,
        allow_null=True)
    organization = serializers.PrimaryKeyRelatedField(
        queryset=OrganizationStructure.objects.using(settings.READONLY_DATABASE))
    model = serializers.CharField(max_length=50, required=True)
    serie = serializers.CharField(max_length=50)
    plaque = serializers.CharField(max_length=50)

    def validate(self, data):
        data = super().validate(data)
        org_pk_view = self.context['view'].org_pk
        obj_type = data['type']
        organization = data['organization']

        if obj_type != Object.EQUIPMENT:
            logger.debug(
                f'ValidateEquipmentSerializer --> type ({obj_type}) != Object.EQUIPMENT ({Object.EQUIPMENT})')
            raise serializers.ValidationError(
                {'type': _("Type equipment object is not valid.")})

        if organization.pk != org_pk_view:
            logger.debug(
                f'ValidateEquipmentSerializer --> organization.pk ({organization.pk}) != org_pk_view ({org_pk_view})')
            raise serializers.ValidationError(
                {'organization': _("Organization is not valid.")})

        return data

    class Meta:
        model = Object
        fields = "__all__"


class ValidateEquipmentCharacteristicsSerializer(serializers.ModelSerializer):
    object = serializers.PrimaryKeyRelatedField(queryset=Object.objects.using(
        settings.READONLY_DATABASE),
        allow_empty=True, allow_null=True, required=False)
    use_manual = ChunkedFileField(allow_null=True, required=False,
                                  allow_empty_file=True)
    calibration_required = serializers.BooleanField(required=False)
    operation_voltage = serializers.CharField(max_length=40, allow_null=True,
                                              allow_blank=True)
    operation_amperage = serializers.CharField(max_length=40, allow_null=True,
                                               allow_blank=True)
    providers = serializers.PrimaryKeyRelatedField(many=True,
                                                   queryset=Provider.objects.using(
                                                       settings.READONLY_DATABASE),
                                                   required=True, allow_empty=False)
    use_specials_conditions = serializers.CharField(allow_null=True, allow_blank=True,
                                                    required=False)
    generate_pathological_waste = serializers.BooleanField(required=False)
    clean_period_according_to_provider = serializers.IntegerField(min_value=0, allow_null=True)
    instrumental_family = serializers.PrimaryKeyRelatedField(
        queryset=Catalog.objects.using(
            settings.READONLY_DATABASE),
        allow_empty=True, allow_null=True)
    equipment_type = serializers.PrimaryKeyRelatedField(
        queryset=EquipmentType.objects.using(
            settings.READONLY_DATABASE),
        allow_empty=True, allow_null=True)

    def validate(self, data):
        data = super().validate(data)
        lab_pk = self.context.get("lab_pk")
        providers = data['providers']

        for provider in providers:
            if provider.laboratory and provider.laboratory.pk != lab_pk:
                logger.debug(
                    f'ValidateEquipmentCharacteristicsSerializer --> provider.laboratory.pk ({provider.laboratory.pk}) != lab_pk ({lab_pk})')
                raise serializers.ValidationError(
                    {'providers': _("Providers list is not valid.")})
        return data

    class Meta:
        model = EquipmentCharacteristics
        fields = "__all__"


class ObjDisplayNameSerializer(GTS2SerializerBase):
    display_fields = 'name'


class ObjDisplayDescriptionSerializer(GTS2SerializerBase):
    display_fields = 'description'


class EquipmentSerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    features = ObjDisplayNameSerializer(many=True)
    use_manual = serializers.SerializerMethodField()
    calibration_required = serializers.SerializerMethodField()
    operation_voltage = serializers.SerializerMethodField()
    operation_amperage = serializers.SerializerMethodField()
    providers = serializers.SerializerMethodField()
    use_specials_conditions = serializers.SerializerMethodField()
    generate_pathological_waste = serializers.SerializerMethodField()
    clean_period_according_to_provider = serializers.SerializerMethodField()
    instrumental_family = serializers.SerializerMethodField()
    equipment_type = serializers.SerializerMethodField()

    def get_use_manual(self, obj):
        if hasattr(obj, 'equipmentcharacteristics') and obj.equipmentcharacteristics:
            file_value = obj.equipmentcharacteristics.use_manual
            return ChunkedFileField().to_representation(file_value)
        return None

    def get_calibration_required(self, obj):
        if hasattr(obj, 'equipmentcharacteristics') and obj.equipmentcharacteristics:
            return obj.equipmentcharacteristics.calibration_required
        return False

    def get_operation_voltage(self, obj):
        if hasattr(obj, 'equipmentcharacteristics') and obj.equipmentcharacteristics:
            return obj.equipmentcharacteristics.operation_voltage
        return ""

    def get_operation_amperage(self, obj):
        if hasattr(obj, 'equipmentcharacteristics') and obj.equipmentcharacteristics:
            return obj.equipmentcharacteristics.operation_amperage
        return ""

    def get_providers(self, obj):
        if hasattr(obj, 'equipmentcharacteristics') and obj.equipmentcharacteristics:
            providers = obj.equipmentcharacteristics.providers.all()
            if providers:
                return [{'id': provider.pk, 'text': provider.name, 'disabled': False,
                         'selected': True} for provider in providers]
        return None

    def get_use_specials_conditions(self, obj):
        if hasattr(obj, 'equipmentcharacteristics') and obj.equipmentcharacteristics:
            return obj.equipmentcharacteristics.use_specials_conditions
        return ""

    def get_generate_pathological_waste(self, obj):
        if hasattr(obj, 'equipmentcharacteristics') and obj.equipmentcharacteristics:
            return obj.equipmentcharacteristics.generate_pathological_waste
        return False

    def get_clean_period_according_to_provider(self, obj):
        if hasattr(obj, 'equipmentcharacteristics') and obj.equipmentcharacteristics:
            return obj.equipmentcharacteristics.clean_period_according_to_provider
        return ""

    def get_instrumental_family(self, obj):
        if hasattr(obj, 'equipmentcharacteristics') and obj.equipmentcharacteristics:
            instrumental_family = obj.equipmentcharacteristics.instrumental_family
            if instrumental_family:
                return {'id': instrumental_family.pk,
                        'text': instrumental_family.description, 'disabled': False,
                        'selected': True}
        return None

    def get_equipment_type(self, obj):
        if hasattr(obj, 'equipmentcharacteristics') and obj.equipmentcharacteristics:
            equipment_type = obj.equipmentcharacteristics.equipment_type
            if equipment_type:
                return {'id': equipment_type.pk, 'text': equipment_type.name,
                        'disabled': False, 'selected': True}
        return None

    def get_actions(self, obj):
        user = self.context["request"].user
        action_list = {
            "create": ["laboratory.add_object", "laboratory.view_object"],
            "update": ["laboratory.change_object", "laboratory.view_object"],
            "destroy": ["laboratory.delete_object", "laboratory.view_object"],
            "detail": ["laboratory.view_object"]
        }
        return get_actions_by_perms(user, action_list)

    class Meta:
        model = Object
        fields = ['id', 'code', 'name', 'synonym', 'is_public', 'description',
                  'features',
                  'type', 'organization', 'created_by', 'model', 'serie', 'plaque',
                  'use_manual', 'calibration_required', 'operation_voltage',
                  'operation_amperage', 'use_specials_conditions',
                  'generate_pathological_waste', 'clean_period_according_to_provider',
                  'instrumental_family', 'equipment_type', 'providers', 'actions']


class EquipmentDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=EquipmentSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class EquipmentTypeSerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    delete_msg = serializers.SerializerMethodField()

    def get_actions(self, obj):
        return {}

    def get_delete_msg(self, obj):
        delete_msg = (_("Deleting the"), _("equipment type"), "<b>"+obj.name+"</b>",
                                 _("implies also deleting all equipment related to it."))

        if not self.context['request'].user.profile.language == "es":
            delete_msg = list(delete_msg)
            delete_msg[0] = _("Deleting")
            delete_msg[1] = "<b>"+obj.name+"</b>"
            delete_msg[2] = _("equipment type")
            delete_msg = tuple(delete_msg)

        return "%s %s %s %s" % delete_msg

    class Meta:
        model = EquipmentType
        fields = ['id', 'name', 'description', 'actions', 'delete_msg']


class EquipmentTypeDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=EquipmentTypeSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class InstrumentalFamilySerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()

    def get_actions(self, obj):
        return {}

    class Meta:
        model = Catalog
        fields = ['description', 'id', 'actions']


class InstrumentalFamilyDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=InstrumentalFamilySerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)

class PrecursorSerializer(serializers.Serializer):
    pk = serializers.IntegerField()


class MaterialSerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    features = ObjDisplayNameSerializer(many=True)
    capacity = serializers.SerializerMethodField()
    capacity_measurement_unit = serializers.SerializerMethodField()

    def get_capacity(self, obj):
        if hasattr(obj,'materialcapacity') and obj.materialcapacity:
            return obj.materialcapacity.capacity
        return ""

    def get_capacity_measurement_unit(self, obj):
        if hasattr(obj, 'materialcapacity') and obj.materialcapacity:
            capacity_measurement_unit = obj.materialcapacity.capacity_measurement_unit
            if capacity_measurement_unit:
                return {'id': capacity_measurement_unit.pk,
                        'text': capacity_measurement_unit.description, 'disabled': False,
                        'selected': True}
        return None

    def get_actions(self, obj):
        user = self.context["request"].user
        action_list = {
            "create": ["laboratory.add_object", "laboratory.view_object"],
            "update": ["laboratory.change_object", "laboratory.view_object"],
            "destroy": ["laboratory.delete_object", "laboratory.view_object"],
            "detail": ["laboratory.view_object"]
        }
        return get_actions_by_perms(user, action_list)

    class Meta:
        model = Object
        fields = ['id', 'code', 'name', 'synonym', 'is_public', 'description',
                  'features',
                  'type', 'organization', 'created_by', 'is_container',
                  'capacity', 'capacity_measurement_unit', 'actions']


class ValidateMaterialCapacitySerializer(serializers.ModelSerializer):
    object = serializers.PrimaryKeyRelatedField(queryset=Object.objects.using(
        settings.READONLY_DATABASE),
        allow_empty=True, allow_null=True, required=False)
    capacity = serializers.FloatField(min_value=1)
    capacity_measurement_unit = serializers.PrimaryKeyRelatedField(queryset=Catalog.objects.filter(key='units'))

    def validate(self, data):
        data = super().validate(data)
        material_object = data.get('object')

        if material_object and material_object.type != Object.MATERIAL:
            logger.debug(
                f'ValidateMaterialCapacitySerializer --> type ({material_object.type}) != Object.MATERIAL ({Object.MATERIAL})'
            )
            raise serializers.ValidationError(
                {'type': _("Type object is not valid.")}
            )
        return data

    class Meta:
        model = MaterialCapacity
        fields = "__all__"

class ValidateMaterialSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=255)
    synonym = serializers.CharField(max_length=255, allow_null=True, allow_blank=True,
                                    required=False)
    description = serializers.CharField(allow_null=True, allow_blank=True,
                                        required=False)
    type = serializers.CharField(max_length=2, default=Object.MATERIAL)
    is_public = serializers.BooleanField(required=False)
    is_container = serializers.BooleanField(required=False)
    features = serializers.PrimaryKeyRelatedField(many=True,
                                                  queryset=ObjectFeatures.objects.using(
                                                      settings.READONLY_DATABASE),
                                                  required=True, allow_empty=False)
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.using(settings.READONLY_DATABASE), allow_empty=True,
        allow_null=True)
    organization = serializers.PrimaryKeyRelatedField(
        queryset=OrganizationStructure.objects.using(settings.READONLY_DATABASE))

    def validate(self, data):
        data = super().validate(data)
        obj_type = data['type']

        if obj_type != Object.MATERIAL:
            logger.debug(
                f'ValidateMaterialSerializer --> type ({obj_type}) != Object.MATERIAL ({Object.MATERIAL})')
            raise serializers.ValidationError(
                {'type': _("Type object is not valid.")})

        return data

    class Meta:
        model = Object
        fields = "__all__"

class MaterialDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=MaterialSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)
