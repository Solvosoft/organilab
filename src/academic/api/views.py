from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from academic.api import serializers
from sga.models import ReviewSubstance


class ReviewSubstanceViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ReviewSubstanceDataTableSerializer
    queryset = ReviewSubstance.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['substance__creator__username', 'substance__creator__first_name', 'substance__creator__last_name', 'substance__comercial_name']
    filterset_class = serializers.ReviewSubstanceFilterSet
    ordering_fields = ['pk']
    ordering = ('pk', )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        org_pk = self.request.GET.get('org_pk', None)
        showapprove = self.request.GET.get('showapprove', None)

        if org_pk:
            queryset = queryset.filter(substance__organization__pk=org_pk)

            if showapprove is not None:
                if eval(showapprove):
                    queryset = queryset.filter(is_approved=True)
                else:
                    queryset = queryset.filter(is_approved=False)
                return queryset
        queryset = queryset.none()
        return queryset


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {'data': data, 'recordsTotal': ReviewSubstance.objects.count(), 'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}
        return Response(self.get_serializer(response).data)