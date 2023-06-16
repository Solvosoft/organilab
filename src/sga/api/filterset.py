from django.db.models.expressions import Value
from django.db.models.functions import Concat
from django.utils import formats
from django_filters import DateTimeFromToRangeFilter
from django_filters import FilterSet, CharFilter
from django.db.models import Q
from djgentelella.fields.drfdatetime import DateTimeRangeTextWidget

from sga.models import ReviewSubstance
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
    comercial_name = CharFilter(field_name='created_by', method='filter_comercial_name')

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

    """
    @property
    def qs(self):
        queryset = super().qs
        name = self.request.GET.get('created_by__icontains')
        if name:
            queryset = queryset.annotate(
                fullname=Concat('substance__created_by__first_name', Value(' '),
                                'substance__created_by__last_name'))
            queryset = queryset.filter(Q(fullname__icontains=name) | Q(
                substance__created_by__username__icontains=name)).distinct()
        return queryset
    """
