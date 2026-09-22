from django_filters import DateFromToRangeFilter, FilterSet
from djgentelella.fields.drfdatetime import DateRangeTextWidget

from ambiental.models import ConsumptionAlert, ConsumptionRecord, MeasurementPoint, NormalizationBase


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
        widget=DateRangeTextWidget(attrs={"placeholder": "YYYY/MM/DD"})
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


class NormalizationBaseFilter(FilterSet):
    class Meta:
        model = NormalizationBase
        fields = {
            "normalizer": ["exact"],
            "building": ["exact"],
            "year": ["exact"],
            "is_manual": ["exact"],
        }


class ConsumptionAlertFilter(FilterSet):
    class Meta:
        model = ConsumptionAlert
        fields = {
            "point": ["exact"],
            "point__building": ["exact"],
            "reviewed": ["exact"],
            "level": ["exact"],
            "message": ["icontains"],
        }
