from django_filters import FilterSet

from sga.models import Substance


class SubstanceFilterSet(FilterSet):

    class Meta:
        model = Substance
        fields = ['comercial_name', 'uipa_name']