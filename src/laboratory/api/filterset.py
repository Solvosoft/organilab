from django.db.models import Q
from django_filters import FilterSet
from django.db.models.functions import Concat
from sga.models import Substance
from django.db.models.expressions import Value


class SubstanceFilterSet(FilterSet):

    def filter_queryset(self, queryset):
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.annotate(
                fullname=Concat('created_by__first_name', Value(' '),
                                'created_by__last_name'))
            queryset = queryset.filter(
                Q(created_by__username__icontains=search) |
                Q(fullname__icontains=search) |
                Q(comercial_name__icontains=search) |
                Q(uipa_name__icontains=search)).distinct()
        return queryset


    class Meta:
        model = Substance
        fields = ['created_by','comercial_name', 'uipa_name']
