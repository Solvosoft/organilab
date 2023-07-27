from django.db.models.expressions import Value
from django.db.models.functions import Concat
from django.utils import formats
from django_filters import DateTimeFromToRangeFilter
from django_filters import FilterSet, CharFilter
from django.db.models import Q
from djgentelella.fields.drfdatetime import DateTimeRangeTextWidget

from sga.models import ReviewSubstance, DisplayLabel, RecipientSize
from sga.models import Substance


class SubstanceFilterSet(FilterSet):
    class Meta:
        model = Substance
        fields = ['comercial_name', 'uipa_name']


class ReviewSubstanceFilterSet(FilterSet):
    creation_date = DateTimeFromToRangeFilter(
        widget=DateTimeRangeTextWidget(
            attrs={'placeholder': formats.get_format('DATETIME_INPUT_FORMATS')[0]}))
    created_by = CharFilter(field_name='created_by', method='filter_user')
    comercial_name = CharFilter(field_name='comercial_name', method='filter_comercial_name')

    def filter_user(self, queryset, name, value):
        return queryset.filter(Q(created_by__first_name__icontains=value) | Q(
            created_by__last_name__icontains=value) | Q(
            created_by__username__icontains=value))

    def filter_comercial_name(self, queryset, name, value):
        if value:
            return queryset.filter(substance__comercial_name__icontains=value)
        return queryset

    class Meta:
        model = ReviewSubstance
        fields = ['comercial_name', 'creation_date', 'created_by']


class DisplayLabelFilterSet(FilterSet):
    creation_date = DateTimeFromToRangeFilter(
        widget=DateTimeRangeTextWidget(
            attrs={'placeholder': formats.get_format('DATETIME_INPUT_FORMATS')[0]}))
    created_by = CharFilter(field_name='created_by', method='filter_user')

    def filter_user(self, queryset, name, value):
        return queryset.filter(Q(created_by__first_name__icontains=value) | Q(
            created_by__last_name__icontains=value) | Q(
            created_by__username__icontains=value))

    class Meta:
        model = DisplayLabel
        fields = ['name', 'creation_date', 'created_by']

class RecipientsFilterSet(FilterSet):

    def filter_queryset(self, queryset):
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(width__icontains=search) |
                Q(height__icontains=search)).distinct()
        return queryset

    class Meta:
        model = RecipientSize
        fields = ['name', 'width', 'height']
