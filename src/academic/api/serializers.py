import logging

from django.db.models import Q
from django.utils import formats
from django.utils.translation import gettext_lazy as _
from django_filters import DateTimeFromToRangeFilter
from django_filters import FilterSet, CharFilter
from djgentelella.fields.drfdatetime import DateTimeRangeTextWidget
from rest_framework import serializers

from academic.models import CommentProcedureStep

logger = logging.getLogger('organilab')


class ProcedureStepCommentFilterSet(FilterSet):
    creator_at = DateTimeFromToRangeFilter(
        widget=DateTimeRangeTextWidget(
            attrs={'placeholder': formats.get_format('DATETIME_INPUT_FORMATS')[0]}))
    creator = CharFilter(field_name='creator', method='filter_user')

    def filter_user(self, queryset, name, value):
        return queryset.filter(Q(creator__first_name__icontains=value) | Q(
            creator__last_name__icontains=value) | Q(
            creator__username__icontains=value))

    class Meta:
        model = CommentProcedureStep
        fields = ['creator', 'creator_at', 'comment']


class ProcedureStepCommentSerializer(serializers.ModelSerializer):
    creator = serializers.SerializerMethodField(required=False)
    creator_at = serializers.DateTimeField(required=False, format=
    formats.get_format('DATETIME_INPUT_FORMATS')[0])

    def get_creator(self, obj):
        try:
            if not obj:
                return _("No user found")
            if not obj.creator:
                return _("No user found")

            name = obj.creator.get_full_name()
            if not name:
                name = obj.creator.username
            return name
        except AttributeError:
            return _("No user found")

    class Meta:
        model = CommentProcedureStep
        fields = '__all__'


class ProcedureStepCommentDatatableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ProcedureStepCommentSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)




