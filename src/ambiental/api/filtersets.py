from django_filters import FilterSet

from ambiental.models import MeasurementPoint


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
