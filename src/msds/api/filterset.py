from django_filters import rest_framework as filters

from sga.models import SDSTraceability


class SDSTraceabilityFilterSet(filters.FilterSet):

    class Meta:
        model = SDSTraceability
        fields = {
            "is_verified": ["exact"],
            "source": ["icontains"],
            "verified_date": ["exact"],
            "sga_substance_characteristics__cas_id_number": ["icontains"],
            "sga_substance_characteristics__object_related__name": ["icontains"],
        }
