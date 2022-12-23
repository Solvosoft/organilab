from django.contrib.admin.models import LogEntry
from django.urls import reverse
from rest_framework import serializers

from laboratory.models import CommentInform
from reservations_management.models import ReservedProducts, Reservations
from organilab.settings import DATETIME_INPUT_FORMATS
from laboratory.models import Protocol
from django.utils.translation import gettext_lazy as _

from django_filters import DateFromToRangeFilter, DateTimeFromToRangeFilter, filters
from djgentelella.fields.drfdatetime import DateRangeTextWidget, DateTimeRangeTextWidget
from django_filters import FilterSet


class ReservedProductsSerializer(serializers.ModelSerializer):
    initial_date = serializers.DateTimeField(input_formats=DATETIME_INPUT_FORMATS, required=False)
    final_date = serializers.DateTimeField(input_formats=DATETIME_INPUT_FORMATS, required=False)

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
        org_pk = self.context['view'].kwargs.get('org_pk', 0)
        btn = ''
        if user.has_perm('laboratory.change_protocol'):
            btn += "<a href=\"%s\" class='btn btn-outline-warning btn-sm'><i class='fa fa-edit' aria-hidden='true'></i> %s</a>"%(
                reverse('laboratory:protocol_update', args=(obj.laboratory.pk,org_pk, obj.pk)),
                _("Edit")
            )
        if user.has_perm('laboratory.delete_protocol'):
            btn += "<a href=\"%s\" class='btn btn-outline-danger btn-sm'><i class='fa fa-trash' aria-hidden='true'></i> %s</a>"%(
                reverse('laboratory:protocol_delete', args=(obj.laboratory.pk,org_pk, obj.pk)),
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


class LogEntrySerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    action_flag = serializers.SerializerMethodField()
    action_time = serializers.DateTimeField(format=DATETIME_INPUT_FORMATS[0])

    def get_user(self, obj):
        if not obj:
            return _("No user found")

        name = obj.user.get_full_name()
        if not name:
            name = obj.username
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

