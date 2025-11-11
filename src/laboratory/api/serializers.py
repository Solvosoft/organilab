import logging

from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from djgentelella.fields.files import ChunkedFileField
from djgentelella.serializers import GTDateField
from djgentelella.serializers.selects import GTS2SerializerBase
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from auth_and_perms.organization_utils import (
    user_is_allowed_on_organization,
    organization_can_change_laboratory,
)
from laboratory.models import (
    CommentInform,
    Inform,
    ShelfObject,
    OrganizationStructure,
    Shelf,
    Laboratory,
    ShelfObjectObservation,
    Object,
    ObjectFeatures,
    Provider,
    Catalog,
    EquipmentType,
    EquipmentCharacteristics,
    SustanceCharacteristics, ReactiveLimit, ObjectMaximumLimit,
)
from laboratory.models import Protocol
from laboratory.utils import get_actions_by_perms, get_users_from_organization
from organilab.settings import DATETIME_INPUT_FORMATS
from reservations_management.models import ReservedProducts, Reservations
from sga.models import DangerIndication

logger = logging.getLogger("organilab")


class ReservedProductsSerializer(serializers.ModelSerializer):
    initial_date = serializers.DateTimeField(input_formats=DATETIME_INPUT_FORMATS)
    final_date = serializers.DateTimeField(input_formats=DATETIME_INPUT_FORMATS)

    class Meta:
        model = ReservedProducts
        fields = "__all__"


class ReservedProductsSerializerUpdate(serializers.ModelSerializer):
    class Meta:
        model = ReservedProducts
        fields = ["reservation", "status"]


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservations
        fields = "__all__"


class CommentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentInform
        fields = "__all__"


class ProtocolSerializer(serializers.ModelSerializer):
    action = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()

    def get_file(self, obj):
        if not obj:
            return {"url": "#", "display_name": _("File not found")}

        return {
            "url": obj.file.url,
            "class": "btn btn-sm btn-outline-success",
            "display_name": "<i class='fa fa-download' aria-hidden='true'></i> %s"
            % _("Download"),
        }

    def get_action(self, obj):
        user = self.context["request"].user
        org_pk = self.context["request"].GET["org_pk"]
        btn = ""
        if user.has_perm("laboratory.change_protocol"):
            btn += (
                "<a href=\"%s\" class='btn btn-outline-warning btn-sm'><i class='fa fa-edit' aria-hidden='true'></i> %s</a>"
                % (
                    reverse(
                        "laboratory:protocol_update",
                        args=(org_pk, obj.laboratory.pk, obj.pk),
                    ),
                    _("Edit"),
                )
            )
        if user.has_perm("laboratory.delete_protocol"):
            btn += (
                "<a href=\"%s\" class='btn btn-outline-danger btn-sm'><i class='fa fa-trash' aria-hidden='true'></i> %s</a>"
                % (
                    reverse(
                        "laboratory:protocol_delete",
                        args=(org_pk, obj.laboratory.pk, obj.pk),
                    ),
                    _("Delete"),
                )
            )

        return btn

    class Meta:
        model = Protocol
        fields = ["name", "short_description", "file", "action"]


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
        return ""

    class Meta:
        model = LogEntry
        fields = "__all__"


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
        fields = "__all__"


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
        if obj and self.context["request"].user.has_perm("laboratory.add_inform"):
            return """
                    <a href="%s"><i class="fa fa-eye" aria-hidden="true"></i></a>
                    """ % (
                reverse(
                    "laboratory:complete_inform",
                    kwargs={
                        "org_pk": self.context["view"].kwargs["pk"],
                        "lab_pk": obj.object_id,
                        "pk": obj.pk,
                    },
                )
            )
        return ""

    class Meta:
        model = Inform
        fields = [
            "name",
            "start_application_date",
            "close_application_date",
            "status",
            "action",
        ]


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
            return _("Unknown")

    def get_container(self, obj):
        if obj.container:
            return obj.container.object.name
        return ""


class ShelfObjectSerialize(BaseShelfObjectSerializer, serializers.ModelSerializer):
    action = serializers.SerializerMethodField()
    object_name = serializers.SerializerMethodField()
    unit = serializers.SerializerMethodField()
    last_update = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    def get_action(self, obj):
        if obj:
            org_pk = self.context["org_pk"]
            if obj.created_by:
                return """
                        <a href="%s" class="btn btn-secondary" target="_blank"><i class="fa fa-eye" aria-hidden="true"></i></a>
                        """ % (
                    reverse(
                        "laboratory:profile_detail",
                        kwargs={"org_pk": org_pk, "pk": obj.created_by.pk},
                    )
                )
            else:
                return ""
        return ""

    class Meta:
        model = ShelfObject
        fields = [
            "object_name",
            "unit",
            "quantity",
            "last_update",
            "created_by",
            "action",
        ]


class ShelfPkList(serializers.Serializer):
    shelfs = serializers.ListField(
        child=serializers.IntegerField(), allow_null=False, allow_empty=False
    )


class ShelfObjectLaboratoryViewSerializer(
    BaseShelfObjectSerializer, serializers.ModelSerializer
):
    object_type = serializers.SerializerMethodField()
    object_name = serializers.SerializerMethodField()
    unit = serializers.SerializerMethodField()
    last_update = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    container = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    def get_actions(self, obj):
        context = {
            "laboratory": self.context["view"].laboratory,
            "org_pk": self.context["view"].organization,
            "shelfobject": obj,
        }
        return render_to_string(
            "laboratory/serializers/shelfobject_actions.html",
            request=self.context["request"],
            context=context,
        )

    class Meta:
        model = ShelfObject
        fields = [
            "pk",
            "object_type",
            "object_name",
            "unit",
            "quantity",
            "last_update",
            "created_by",
            "container",
            "actions",
        ]


class ShelfObjectTableSerializer(serializers.Serializer):
    data = serializers.ListField(
        child=ShelfObjectLaboratoryViewSerializer(), required=True
    )
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class BaseOrganizationLaboratory(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(
        queryset=OrganizationStructure.objects.using(settings.READONLY_DATABASE)
    )
    laboratory = serializers.PrimaryKeyRelatedField(
        queryset=Laboratory.objects.using(settings.READONLY_DATABASE)
    )

    def validate_organization(self, value):
        user_is_allowed_on_organization(self.user, value)
        return value

    def validate(self, value):
        if not organization_can_change_laboratory(
            value["laboratory"], value["organization"]
        ):
            raise ValidationError(detail="Wrong Laboratory")
        return value

    user = None

    def set_user(self, user):
        self.user = user


class ShelfLabViewSerializer(serializers.Serializer):
    shelf = serializers.PrimaryKeyRelatedField(
        queryset=Shelf.objects.using(settings.READONLY_DATABASE), required=False
    )

    def __init__(self, *args, **kwargs):
        self.laboratory = kwargs.pop("laboratory")
        super().__init__(*args, **kwargs)

    def validate(self, value):
        value = super().validate(value)
        if "shelf" not in value:
            value["shelf"] = None

        if value["shelf"] is not None:
            if self.laboratory != value["shelf"].furniture.labroom.laboratory:
                raise ValidationError(detail="Shelf not found on Laboratory")
        return value


class CreateObservationShelfObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShelfObjectObservation
        fields = ["action_taken", "description"]


class ValidateEquipmentSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=255)
    synonym = serializers.CharField(
        max_length=255, allow_null=True, allow_blank=True, required=False
    )
    description = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    type = serializers.CharField(max_length=2)
    is_public = serializers.BooleanField(required=False)
    features = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ObjectFeatures.objects.using(settings.READONLY_DATABASE),
        required=True,
        allow_empty=False,
    )
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.using(settings.READONLY_DATABASE),
        allow_empty=True,
        allow_null=True,
    )
    organization = serializers.PrimaryKeyRelatedField(
        queryset=OrganizationStructure.objects.using(settings.READONLY_DATABASE)
    )
    model = serializers.CharField(max_length=50, required=True)
    serie = serializers.CharField(max_length=50)
    plaque = serializers.CharField(max_length=50)

    def validate(self, data):
        data = super().validate(data)
        org_pk_view = self.context["view"].org_pk
        obj_type = data["type"]
        organization = data["organization"]

        if obj_type != Object.EQUIPMENT:
            logger.debug(
                f"ValidateEquipmentSerializer --> type ({obj_type}) != Object.EQUIPMENT ({Object.EQUIPMENT})"
            )
            raise serializers.ValidationError(
                {"type": _("Type equipment object is not valid.")}
            )

        if organization.pk != org_pk_view:
            logger.debug(
                f"ValidateEquipmentSerializer --> organization.pk ({organization.pk}) != org_pk_view ({org_pk_view})"
            )
            raise serializers.ValidationError(
                {"organization": _("Organization is not valid.")}
            )

        return data

    class Meta:
        model = Object
        fields = "__all__"


class ValidateEquipmentCharacteristicsSerializer(serializers.ModelSerializer):
    object = serializers.PrimaryKeyRelatedField(
        queryset=Object.objects.using(settings.READONLY_DATABASE),
        allow_empty=True,
        allow_null=True,
        required=False,
    )
    use_manual = ChunkedFileField(
        allow_null=True, required=False, allow_empty_file=True
    )
    calibration_required = serializers.BooleanField(required=False)
    operation_voltage = serializers.CharField(
        max_length=40, allow_null=True, allow_blank=True
    )
    operation_amperage = serializers.CharField(
        max_length=40, allow_null=True, allow_blank=True
    )
    providers = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Provider.objects.using(settings.READONLY_DATABASE),
        required=True,
        allow_empty=False,
    )
    use_specials_conditions = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    generate_pathological_waste = serializers.BooleanField(required=False)
    clean_period_according_to_provider = serializers.IntegerField(
        min_value=0, allow_null=True
    )
    instrumental_family = serializers.PrimaryKeyRelatedField(
        queryset=Catalog.objects.using(settings.READONLY_DATABASE),
        allow_empty=True,
        allow_null=True,
    )
    equipment_type = serializers.PrimaryKeyRelatedField(
        queryset=EquipmentType.objects.using(settings.READONLY_DATABASE),
        allow_empty=True,
        allow_null=True,
    )

    def validate(self, data):
        data = super().validate(data)
        lab_pk = self.context.get("lab_pk")
        providers = data["providers"]

        for provider in providers:
            if provider.laboratory and provider.laboratory.pk != lab_pk:
                logger.debug(
                    f"ValidateEquipmentCharacteristicsSerializer --> provider.laboratory.pk ({provider.laboratory.pk}) != lab_pk ({lab_pk})"
                )
                raise serializers.ValidationError(
                    {"providers": _("Providers list is not valid.")}
                )
        return data

    class Meta:
        model = EquipmentCharacteristics
        fields = "__all__"


class ObjDisplayNameSerializer(GTS2SerializerBase):
    display_fields = "name"


class ObjDisplayDescriptionSerializer(GTS2SerializerBase):
    display_fields = "description"


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
        if hasattr(obj, "equipmentcharacteristics") and obj.equipmentcharacteristics:
            file_value = obj.equipmentcharacteristics.use_manual
            return ChunkedFileField().to_representation(file_value)
        return None

    def get_calibration_required(self, obj):
        if hasattr(obj, "equipmentcharacteristics") and obj.equipmentcharacteristics:
            return obj.equipmentcharacteristics.calibration_required
        return False

    def get_operation_voltage(self, obj):
        if hasattr(obj, "equipmentcharacteristics") and obj.equipmentcharacteristics:
            return obj.equipmentcharacteristics.operation_voltage
        return ""

    def get_operation_amperage(self, obj):
        if hasattr(obj, "equipmentcharacteristics") and obj.equipmentcharacteristics:
            return obj.equipmentcharacteristics.operation_amperage
        return ""

    def get_providers(self, obj):
        if hasattr(obj, "equipmentcharacteristics") and obj.equipmentcharacteristics:
            providers = obj.equipmentcharacteristics.providers.all()
            if providers:
                return [
                    {
                        "id": provider.pk,
                        "text": provider.name,
                        "disabled": False,
                        "selected": True,
                    }
                    for provider in providers
                ]
        return None

    def get_use_specials_conditions(self, obj):
        if hasattr(obj, "equipmentcharacteristics") and obj.equipmentcharacteristics:
            return obj.equipmentcharacteristics.use_specials_conditions
        return ""

    def get_generate_pathological_waste(self, obj):
        if hasattr(obj, "equipmentcharacteristics") and obj.equipmentcharacteristics:
            return obj.equipmentcharacteristics.generate_pathological_waste
        return False

    def get_clean_period_according_to_provider(self, obj):
        if hasattr(obj, "equipmentcharacteristics") and obj.equipmentcharacteristics:
            return obj.equipmentcharacteristics.clean_period_according_to_provider
        return ""

    def get_instrumental_family(self, obj):
        if hasattr(obj, "equipmentcharacteristics") and obj.equipmentcharacteristics:
            instrumental_family = obj.equipmentcharacteristics.instrumental_family
            if instrumental_family:
                return {
                    "id": instrumental_family.pk,
                    "text": instrumental_family.description,
                    "disabled": False,
                    "selected": True,
                }
        return None

    def get_equipment_type(self, obj):
        if hasattr(obj, "equipmentcharacteristics") and obj.equipmentcharacteristics:
            equipment_type = obj.equipmentcharacteristics.equipment_type
            if equipment_type:
                return {
                    "id": equipment_type.pk,
                    "text": equipment_type.name,
                    "disabled": False,
                    "selected": True,
                }
        return None

    def get_actions(self, obj):
        user = self.context["request"].user
        action_list = {
            "create": ["laboratory.add_object", "laboratory.view_object"],
            "update": ["laboratory.change_object", "laboratory.view_object"],
            "destroy": ["laboratory.delete_object", "laboratory.view_object"],
            "detail": ["laboratory.view_object"],
        }
        return get_actions_by_perms(user, action_list)

    class Meta:
        model = Object
        fields = [
            "id",
            "code",
            "name",
            "synonym",
            "is_public",
            "description",
            "features",
            "type",
            "organization",
            "created_by",
            "model",
            "serie",
            "plaque",
            "use_manual",
            "calibration_required",
            "operation_voltage",
            "operation_amperage",
            "use_specials_conditions",
            "generate_pathological_waste",
            "clean_period_according_to_provider",
            "instrumental_family",
            "equipment_type",
            "providers",
            "actions",
        ]


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
        delete_msg = (
            _("Deleting the"),
            _("equipment type"),
            "<b>" + obj.name + "</b>",
            _("implies also deleting all equipment related to it."),
        )

        if not self.context["request"].user.profile.language == "es":
            delete_msg = list(delete_msg)
            delete_msg[0] = _("Deleting")
            delete_msg[1] = "<b>" + obj.name + "</b>"
            delete_msg[2] = _("equipment type")
            delete_msg = tuple(delete_msg)

        return "%s %s %s %s" % delete_msg

    class Meta:
        model = EquipmentType
        fields = ["id", "name", "description", "actions", "delete_msg"]


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
        fields = ["description", "id", "actions"]


class InstrumentalFamilyDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=InstrumentalFamilySerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class PrecursorSerializer(serializers.Serializer):
    pk = serializers.IntegerField()


class ValidateReactiveSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=255)
    synonym = serializers.CharField(
        max_length=255, allow_null=True, allow_blank=True, required=False
    )
    description = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    type = serializers.CharField(max_length=2)
    is_public = serializers.BooleanField(required=False)
    features = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ObjectFeatures.objects.using(settings.READONLY_DATABASE),
        required=True,
        allow_empty=False,
    )
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.using(settings.READONLY_DATABASE),
        allow_empty=True,
        allow_null=True,
    )
    organization = serializers.PrimaryKeyRelatedField(
        queryset=OrganizationStructure.objects.using(settings.READONLY_DATABASE)
    )
    model = serializers.CharField(max_length=50, required=True)
    serie = serializers.CharField(max_length=50)
    plaque = serializers.CharField(max_length=50)
    is_dangerous = serializers.BooleanField(required=False)
    has_threshold = serializers.BooleanField(required=False)
    threshold = serializers.FloatField(default=0.0, required=False)
    reactive_expiration_date = serializers.DateField(required=False)

    def validate(self, data):
        data = super().validate(data)
        org_pk_view = self.context["view"].org_pk
        obj_type = data["type"]
        organization = data["organization"]

        if obj_type != Object.REACTIVE:
            logger.debug(
                f"ValidateReactiveSerializer --> type ({obj_type}) != Object.Reactive ({Object.REACTIVE})"
            )
            raise serializers.ValidationError(
                {"type": _("Type equipment object is not valid.")}
            )

        if organization.pk != org_pk_view:
            logger.debug(
                f"ValidateReactiveSerializer --> organization.pk ({organization.pk}) != org_pk_view ({org_pk_view})"
            )
            raise serializers.ValidationError(
                {"organization": _("Organization is not valid.")}
            )
        return data

    class Meta:
        model = Object
        fields = "__all__"


class ValidateReactiveCharacteristicsSerializer(serializers.ModelSerializer):
    obj = serializers.PrimaryKeyRelatedField(
        queryset=Object.objects.using(settings.READONLY_DATABASE),
        allow_empty=True,
        allow_null=True,
        required=False,
    )

    iarc = serializers.PrimaryKeyRelatedField(
        queryset=Catalog.objects.filter(key="IARC").using(settings.READONLY_DATABASE),
        allow_empty=True,
        allow_null=True,
        required=False,
    )

    imdg = serializers.PrimaryKeyRelatedField(
        queryset=Catalog.objects.filter(key="IDMG").using(settings.READONLY_DATABASE),
        allow_empty=True,
        allow_null=True,
        required=False,
    )

    white_organ = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Catalog.objects.filter(key="white_organ").using(
            settings.READONLY_DATABASE
        ),
        allow_empty=True,
        allow_null=True,
    )

    bioaccumulable = serializers.BooleanField(required=False)

    molecular_formula = serializers.CharField(
        max_length=80, allow_null=True, allow_blank=True
    )

    cas_id_number = serializers.CharField(
        max_length=80, allow_null=True, allow_blank=True, required=False
    )

    security_sheet = ChunkedFileField(
        allow_null=True, required=False, allow_empty_file=True
    )

    is_precursor = serializers.BooleanField(required=False)

    precursor_type = serializers.PrimaryKeyRelatedField(
        queryset=Catalog.objects.filter(key="Precursor").using(
            settings.READONLY_DATABASE
        ),
        allow_empty=True,
        allow_null=True,
    )

    h_code = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=DangerIndication.objects.using(settings.READONLY_DATABASE),
        allow_empty=True,
        allow_null=True,
        required=False,
    )

    ue_code = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Catalog.objects.filter(key="ue_code").using(
            settings.READONLY_DATABASE
        ),
        allow_empty=True,
        allow_null=True,
    )

    nfpa = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Catalog.objects.filter(key="nfpa").using(settings.READONLY_DATABASE),
        allow_empty=True,
        allow_null=True,
        required=False,
    )

    storage_class = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Catalog.objects.filter(key="storage_class").using(
            settings.READONLY_DATABASE
        ),
        allow_empty=True,
        allow_null=True,
    )

    seveso_list = serializers.BooleanField(required=False)

    img_representation = ChunkedFileField(
        allow_null=True, required=False, allow_empty_file=True
    )

    class Meta:
        model = SustanceCharacteristics
        fields = "__all__"


class ReactiveSerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    features = ObjDisplayNameSerializer(many=True)
    iarc = serializers.SerializerMethodField()
    imdg = serializers.SerializerMethodField()
    white_organ = serializers.SerializerMethodField()
    bioaccumulable = serializers.SerializerMethodField()
    molecular_formula = serializers.SerializerMethodField()
    cas_id_number = serializers.SerializerMethodField()
    security_sheet = serializers.SerializerMethodField()
    is_precursor = serializers.SerializerMethodField()
    precursor_type = serializers.SerializerMethodField()
    h_code = serializers.SerializerMethodField()
    ue_code = serializers.SerializerMethodField()
    nfpa = serializers.SerializerMethodField()
    storage_class = serializers.SerializerMethodField()
    seveso_list = serializers.SerializerMethodField()
    img_representation = serializers.SerializerMethodField()
    combined_booleans = serializers.SerializerMethodField()
    maximum_limit = serializers.SerializerMethodField()
    minimum_limit = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()
    maximum_limit_table = serializers.SerializerMethodField()
    minimum_limit_table = serializers.SerializerMethodField()
    measurement_unit_table = serializers.SerializerMethodField()

    def get_reactive_limits(self, obj):
        lab = self.context["kwargs"].get("lab_pk", None)
        reactive = ReactiveLimit.objects.filter(object=obj, laboratory__pk=lab).first()
        return reactive

    def get_measurement_unit(self, obj):
        limit = self.get_reactive_limits(obj)
        if limit:
            return limit.measurement_unit.description
        return None

    def get_maximum_limit(self, obj):
        limit = self.get_reactive_limits(obj)
        if limit:
            return limit.maximum_limit
        return 0.0

    def get_minimum_limit(self, obj):
        limit = self.get_reactive_limits(obj)
        if limit:
            return limit.minimum_limit
        return 0.0

    def get_measurement_unit_table(self, obj):
        limit = self.get_reactive_limits(obj)
        if limit:
            return limit.measurement_unit.description
        return ""

    def get_maximum_limit_table(self, obj):
        limit = self.get_reactive_limits(obj)
        if limit:
            return limit.maximum_limit
        return ""

    def get_minimum_limit_table(self, obj):
        limit = self.get_reactive_limits(obj)
        if limit:
            return limit.minimum_limit
        return ""

    def get_iarc(self, obj):
        if hasattr(obj, "sustancecharacteristics") and obj.sustancecharacteristics:
            iarc = obj.sustancecharacteristics.iarc
            if iarc:
                return {
                    "id": iarc.pk,
                    "text": iarc.description,
                    "disabled": False,
                    "selected": True,
                }
        return None

    def get_imdg(self, obj):
        if hasattr(obj, "sustancecharacteristics") and obj.sustancecharacteristics:
            imdg = obj.sustancecharacteristics.imdg
            if imdg:
                return {
                    "id": imdg.pk,
                    "text": imdg.description,
                    "disabled": False,
                    "selected": True,
                }
        return None

    def get_white_organ(self, obj):
        if hasattr(obj, "sustancecharacteristics") and obj.sustancecharacteristics:
            white_organs = obj.sustancecharacteristics.white_organ.all()
            if white_organs:
                return [
                    {
                        "id": white_organ.pk,
                        "text": white_organ.description,
                        "disabled": False,
                        "selected": True,
                    }
                    for white_organ in white_organs
                ]
        return None

    def get_bioaccumulable(self, obj):
        if hasattr(obj, "sustancecharacteristics") and obj.sustancecharacteristics:
            return obj.sustancecharacteristics.bioaccumulable
        return False

    def get_molecular_formula(self, obj):
        if hasattr(obj, "sustancecharacteristics") and obj.sustancecharacteristics:
            return obj.sustancecharacteristics.molecular_formula
        return ""

    def get_cas_id_number(self, obj):
        if hasattr(obj, "sustancecharacteristics") and obj.sustancecharacteristics:
            return obj.sustancecharacteristics.cas_id_number
        return ""

    def get_security_sheet(self, obj):
        if hasattr(obj, "sustancecharacteristics") and obj.sustancecharacteristics:
            file_value = obj.sustancecharacteristics.security_sheet
            if file_value:
                return ChunkedFileField().to_representation(file_value)
            return None

    def get_is_precursor(self, obj):
        if hasattr(obj, "sustancecharacteristics") and obj.sustancecharacteristics:
            return obj.sustancecharacteristics.is_precursor
        return False

    def get_precursor_type(self, obj):
        if hasattr(obj, "sustancecharacteristics") and obj.sustancecharacteristics:
            precursor_type = obj.sustancecharacteristics.precursor_type
            if precursor_type:
                return {
                    "id": precursor_type.pk,
                    "text": precursor_type.description,
                    "disabled": False,
                    "selected": True,
                }
        return None

    def get_h_code(self, obj):
        if hasattr(obj, "sustancecharacteristics") and obj.sustancecharacteristics:
            h_codes = obj.sustancecharacteristics.h_code.all()
            if h_codes:
                return [
                    {
                        "id": h_code.pk,
                        "text": f"({h_code.pk}) {h_code.description}",
                        "disabled": False,
                        "selected": True,
                    }
                    for h_code in h_codes
                ]
        return None

    def get_ue_code(self, obj):
        if hasattr(obj, "sustancecharacteristics") and obj.sustancecharacteristics:
            ue_codes = obj.sustancecharacteristics.ue_code.all()
            if ue_codes:
                return [
                    {
                        "id": ue_code.pk,
                        "text": ue_code.description,
                        "disabled": False,
                        "selected": True,
                    }
                    for ue_code in ue_codes
                ]
        return None

    def get_nfpa(self, obj):
        if hasattr(obj, "sustancecharacteristics") and obj.sustancecharacteristics:
            nfpas = obj.sustancecharacteristics.nfpa.all()
            if nfpas:
                return [
                    {
                        "id": nfpa.pk,
                        "text": nfpa.description,
                        "disabled": False,
                        "selected": True,
                    }
                    for nfpa in nfpas
                ]
        return None

    def get_storage_class(self, obj):
        if hasattr(obj, "sustancecharacteristics") and obj.sustancecharacteristics:
            storage_classes = obj.sustancecharacteristics.storage_class.all()
            if storage_classes:
                return [
                    {
                        "id": storage_class.pk,
                        "text": storage_class.description,
                        "disabled": False,
                        "selected": True,
                    }
                    for storage_class in storage_classes
                ]
        return None

    def get_seveso_list(self, obj):
        if hasattr(obj, "sustancecharacteristics") and obj.sustancecharacteristics:
            return obj.sustancecharacteristics.seveso_list
        return False

    def get_img_representation(self, obj):
        if hasattr(obj, "sustancecharacteristics") and obj.sustancecharacteristics:
            file_value = obj.sustancecharacteristics.img_representation
            if file_value:
                return ChunkedFileField().to_representation(file_value)
            return None

    def get_combined_booleans(self, obj):
        is_public = (
            '<i class="fa fa-users fa-fw text-success"></i>'
            if obj.is_public
            else '<i class="fa fa-user-times fa-fw text-warning"></i>'
        )
        precursor = '<i class="fa fa-times-circle fa-fw text-warning"></i>'
        bioaccumulable = '<i class="fa fa-flask fa-fw text-warning"></i>'

        if obj.is_public:
            precursor = '<i class="fa fa-check-circle fa-fw text-success"></i>'
        if hasattr(obj, "sustancecharacteristics"):
            if hasattr(obj.sustancecharacteristics, "bioaccumulable"):
                bioaccumulable = '<i class="fa fa-leaf fa-fw text-success"></i>'

        return f"{is_public} {precursor} {bioaccumulable}"

    def get_actions(self, obj):
        user = self.context["request"].user
        action_list = {
            "create": ["laboratory.add_object", "laboratory.view_object"],
            "update": ["laboratory.change_object", "laboratory.view_object"],
            "destroy": ["laboratory.delete_object", "laboratory.view_object"],
            "detail": ["laboratory.view_object"],
            "add_limits": ["laboratory.add_object", "laboratory.view_object"],
            "get_reactive_limits": ["laboratory.view_object"],
        }
        return get_actions_by_perms(user, action_list)

    class Meta:
        model = Object
        fields = [
            "id",
            "code",
            "name",
            "synonym",
            "is_public",
            "description",
            "features",
            "type",
            "organization",
            "created_by",
            "model",
            "serie",
            "plaque",
            "iarc",
            "imdg",
            "white_organ",
            "bioaccumulable",
            "molecular_formula",
            "cas_id_number",
            "security_sheet",
            "is_precursor",
            "precursor_type",
            "h_code",
            "ue_code",
            "nfpa",
            "storage_class",
            "seveso_list",
            "img_representation",
            "combined_booleans",
            "is_dangerous",
            "has_threshold",
            "threshold",
            "actions",
            "is_pure",
            "maximum_limit",
            "minimum_limit",
            "measurement_unit",
            "maximum_limit_table",
            "minimum_limit_table",
            "measurement_unit_table",
        ]


class ReactiveDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ReactiveSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)

    def get_fields(self):
        fields = super().get_fields()
        #fields["data"].child = ReactiveSerializer(context={"lab_pk": self.context["request"]})
        return fields

class GetReactiveLimitSerializer(serializers.ModelSerializer):
    maximum_limit = serializers.FloatField(required=False,default=0.0)
    minimum_limit = serializers.FloatField(required=False,default=0.0)
    measurement_unit = GTS2SerializerBase(required=False)

    class Meta:
        model = ReactiveLimit
        fields = ["maximum_limit", "minimum_limit", "measurement_unit"]

class ReactiveLimitSerializer(serializers.ModelSerializer):
    maximum_limit = serializers.FloatField(required=True)
    minimum_limit = serializers.FloatField(required=True)
    measurement_unit = serializers.PrimaryKeyRelatedField(
        queryset=Catalog.objects.filter(key="units"),
        required=True,
        allow_empty=True,
        allow_null=True,
    )
    laboratory = serializers.PrimaryKeyRelatedField(
        queryset=Laboratory.objects.using(settings.READONLY_DATABASE),
        required=True,
        allow_empty=True,
        allow_null=True,
    )
    object = serializers.PrimaryKeyRelatedField(
        queryset=Object.objects.using(settings.READONLY_DATABASE),
        required=True,
        allow_empty=True,
        allow_null=True,
    )
    class Meta:
        model = ReactiveLimit
        fields = "__all__"
    def validate(self, attrs):
        data = super().validate(attrs)
        if data["maximum_limit"] < data["minimum_limit"]:
            logger.debug(
                f"ReactiveLimitSerializer --> maximum_limit ({data['maximum_limit']}) is lower than minimum_limit ({data['minimum_limit']})"
            )
            raise serializers.ValidationError(
                {"maximum_limit": _("Maximum limit cannot be lower than minimum limit.")}
            )


        return data


class ReactiveLimitsSerializer(serializers.Serializer):
    object = serializers.PrimaryKeyRelatedField(
        many=False,
        required=True,
        queryset=Object.objects.all(),
    )
    laboratory = serializers.PrimaryKeyRelatedField(
        many=False,
        required=True,
        queryset=Laboratory.objects.all(),
    )
    years = serializers.ChoiceField(required=True,
                                    choices=[(i, i) for i in ObjectMaximumLimit.objects.all().values_list("created_at__year", flat=True).distinct()])
