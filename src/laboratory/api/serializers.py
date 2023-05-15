from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.template.loader import render_to_string
from django.urls import reverse
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from auth_and_perms.organization_utils import user_is_allowed_on_organization, organization_can_change_laboratory
from laboratory.models import CommentInform, Inform, ShelfObject, OrganizationStructure, Shelf, Laboratory
from reservations_management.models import ReservedProducts, Reservations
from organilab.settings import DATETIME_INPUT_FORMATS, DATE_INPUT_FORMATS
from laboratory.models import Protocol
from django.utils.translation import gettext_lazy as _

from django_filters import DateFromToRangeFilter, DateTimeFromToRangeFilter, filters
from djgentelella.fields.drfdatetime import DateRangeTextWidget, DateTimeRangeTextWidget
from django_filters import FilterSet


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


class ProtocolFilterSet(FilterSet):

    class Meta:
        model = Protocol
        fields = {}


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
            'display_name': "<i class='fa fa-download' aria-hidden='true'></i> %s" % _("Download")
        }

    def get_action(self, obj):
        user = self.context['request'].user
        org_pk = self.context['request'].GET['org_pk']
        btn = ''
        if user.has_perm('laboratory.change_protocol'):
            btn += "<a href=\"%s\" class='btn btn-outline-warning btn-sm'><i class='fa fa-edit' aria-hidden='true'></i> %s</a>"%(
                reverse('laboratory:protocol_update', args=(org_pk, obj.laboratory.pk, obj.pk)),
                _("Edit")
            )
        if user.has_perm('laboratory.delete_protocol'):
            btn += "<a href=\"%s\" class='btn btn-outline-danger btn-sm'><i class='fa fa-trash' aria-hidden='true'></i> %s</a>"%(
                reverse('laboratory:protocol_delete', args=(org_pk, obj.laboratory.pk, obj.pk)),
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

def find_username(request):
    return None


class LogEntryFilterSet(FilterSet):
    action_time = DateFromToRangeFilter(widget=DateRangeTextWidget(attrs={'placeholder': 'YYYY/MM/DD'}))
    #user = filters.ModelChoiceFilter(queryset=find_username)
    class Meta:
        model = LogEntry
        fields = {
            'object_repr': ['icontains'],
            'change_message': ['icontains'],
            'action_flag': ['exact'],
        }


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
                    """%(
                reverse('laboratory:complete_inform', kwargs={
                    'org_pk': self.context['view'].kwargs['pk'],
                    'lab_pk': obj.object_id,
                    'pk': obj.pk
                })
            )
        return ""

    class Meta:
        model = Inform
        fields = ['name', 'start_application_date', 'close_application_date', 'status', 'action']


class InformDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=InformSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class InformFilterSet(FilterSet):
    class Meta:
        model = Inform
        fields = {'name': ['icontains'], 'status': ['exact']}

class ShelfObjectFilterSet(FilterSet):
    class Meta:
        model = ShelfObject
        fields = {'object__name': ['icontains'] }


class BaseShelfObjectSerializer:

    def get_object_type(self, obj):
        return obj.object.get_type_display()

    def get_object_name(self, obj):
        return obj.object.name

    def get_unit(self, obj):
        return obj.get_measurement_unit_display()

    def get_last_update(self, obj):
        return obj.last_update.date()

    def get_creator(self, obj):
        if obj.creator:
            return str(obj.creator)
        else:
            return _('Unknown')

    def get_container(self, obj):
        obj_container = obj.shelfobjectcontainer_set.first()
        if obj_container:
            return obj_container.container.name
        return ''


class ShelfObjectSerialize(BaseShelfObjectSerializer, serializers.ModelSerializer):
    action = serializers.SerializerMethodField()
    object_name = serializers.SerializerMethodField()
    unit = serializers.SerializerMethodField()
    last_update = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()

    def get_action(self, obj):
        if obj:
            org_pk = self.context['org_pk']
            if obj.creator:
                return """
                        <a href="%s" class="btn btn-secondary" target="_blank"><i class="fa fa-eye" aria-hidden="true"></i></a>
                        """%(
                    reverse('laboratory:profile_detail', kwargs={
                        'org_pk': org_pk,
                        'pk': obj.creator.pk
                    })
                )
            else:
                return ""
        return ""

    class Meta:
        model = ShelfObject
        fields = ['object_name', 'unit','quantity','last_update','creator','action']


class ShelfPkList(serializers.Serializer):
    shelfs=serializers.ListField(child=serializers.IntegerField(), allow_null=False, allow_empty=False)


class ShelfObjectLaboratoryViewSerializer(BaseShelfObjectSerializer, serializers.ModelSerializer):
    object_type = serializers.SerializerMethodField()
    object_name = serializers.SerializerMethodField()
    unit = serializers.SerializerMethodField()
    last_update = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()
    container = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    def get_actions(self, obj):
        context={
            'laboratory': self.context['view'].laboratory,
            'org_pk': self.context['view'].organization,
            'shelfobject': obj
        }
        return render_to_string(
            'laboratory/serializers/shelfobject_actions.html',
            request=self.context['request'],
            context=context
        )

        pass
    class Meta:
        model = ShelfObject
        fields = ['pk','object_type', 'object_name', 'unit','quantity','last_update','creator', 'container', 'actions']


class ShelfObjectTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ShelfObjectLaboratoryViewSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class BaseOrganizationLaboratory(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=OrganizationStructure.objects.using(settings.READONLY_DATABASE))
    laboratory = serializers.PrimaryKeyRelatedField(queryset=Laboratory.objects.using(settings.READONLY_DATABASE))

    def validate_organization(self, value):
        user_is_allowed_on_organization(self.user, value)
        return value

    def validate(self, value):
        if not organization_can_change_laboratory(value['laboratory'], value['organization']):
            raise ValidationError(detail="Wrong Laboratory")
        return value
    user = None

    def set_user(self, user):
        self.user=user


class ShelfLabViewSerializer(serializers.Serializer):
    shelf = serializers.PrimaryKeyRelatedField(queryset=Shelf.objects.using(settings.READONLY_DATABASE), required=False)

    def __init__(self, *args, **kwargs):
        self.laboratory = kwargs.pop('laboratory')
        super().__init__(*args, **kwargs)

    def validate(self, value):
        value = super().validate(value)
        if 'shelf' not in value:
            value['shelf']=None

        if value['shelf'] is not None:
            if self.laboratory != value['shelf'].furniture.labroom.laboratory:
                raise ValidationError(detail="Shelf not found on Laboratory")
        return value