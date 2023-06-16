from django.db.models import Q, Value
from django.db.models.functions import Concat
from django_filters import FilterSet

from academic.models import MyProcedure, Procedure


class MyProcedureFilterSet(FilterSet):

    def filter_queryset(self, queryset):
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.annotate(
                fullname=Concat('created_by__first_name', Value(' '),
                                'created_by__last_name'))
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(fullname__icontains=search) | Q(
                    created_by__username__icontains=search) |
                Q(custom_procedure__title__icontains=search)).distinct()
        return queryset

    class Meta:
        model = MyProcedure
        fields = ['name', 'custom_procedure', 'status', 'created_by']


class ProcedureFilterSet(FilterSet):

    def filter_queryset(self, queryset):
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)).distinct()
        return queryset

    class Meta:
        model = Procedure
        fields = ['title', 'description']
