from django_filters import rest_framework as filters

from laboratory.models import SDSTraceability


class SDSTraceabilityFilterSet(filters.FilterSet):

    class Meta:
        model = SDSTraceability
        fields = {
            "is_verified": ["exact"],
            "source": ["icontains"],
            "verified_date": ["exact"],
            "sustance_characteristics__cas_id_number": ["icontains"],
            "sustance_characteristics__obj__name": ["icontains"],
        }
