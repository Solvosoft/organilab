from django_filters import DateFromToRangeFilter, FilterSet
from djgentelella.fields.drfdatetime import DateRangeTextWidget

from ambiental.models import ConsumptionRecord, MeasurementPoint


class MeasurementPointFilter(FilterSet):
    class Meta:
        model = MeasurementPoint
        fields = {
            "code": ["icontains"],
            "name": ["icontains"],
            "point_type": ["exact"],
            "resource_type": ["exact"],
            "building": ["exact"],
            "laboratories": ["exact"],
        }


class ConsumptionRecordFilter(FilterSet):
    period_end = DateFromToRangeFilter(
        widget=DateRangeTextWidget(attrs={"placeholder": "DD/MM/YYYY/"})
    )

    class Meta:
        model = ConsumptionRecord
        fields = {
            "point": ["exact"],
            "point__building": ["exact"],
            "point__resource_type": ["exact"],
            "is_waste": ["exact"],
            "source": ["exact"],
        }
