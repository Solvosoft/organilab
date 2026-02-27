from django.db.models import Q, Value
from django.db.models.functions import Concat
from django_filters import FilterSet, DateFromToRangeFilter, CharFilter
from djgentelella.fields.drfdatetime import DateRangeTextWidget

from report.models import ObjectChangeLogReportBuilder
from laboratory.models import PrecursorReportValues


class ObjectChangeLogFilterSet(FilterSet):
    def filter_queryset(self, queryset):
        search = self.request.GET.get("search", "")
        if search:
            queryset = queryset.annotate(
                fullname=Concat("user__first_name", Value(" "), "user__last_name")
            )
            queryset = queryset.filter(
                Q(fullname__icontains=search)
                | Q(user__username__icontains=search)
                | Q(new_value__icontains=search)
                | Q(old_value__icontains=search)
                | Q(diff_value__icontains=search)
            ).distinct()
        return queryset

    class Meta:
        model = ObjectChangeLogReportBuilder
        fields = ["user", "new_value", "old_value", "diff_value"]


class PrecursorReportValuesFilter(FilterSet):
    class Meta:
        model = PrecursorReportValues
        fields = {
            "id": ["exact"],
            "precursor_report": ["exact"],
            "object__name": ["icontains"],
            "object__code": ["icontains"],
        }
