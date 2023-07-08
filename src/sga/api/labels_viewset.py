from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins
from rest_framework.authentication import SessionAuthentication
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import OrganizationStructure
from sga.models import DisplayLabel
from . import serializers
from .filterset import DisplayLabelFilterSet


class DisplayLabelViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.DisplayLabelDataTableSerializer
    queryset = DisplayLabel.objects.using(settings.READONLY_DATABASE)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['creation_date', 'created_by', 'name']
    filterset_class = DisplayLabelFilterSet
    ordering_fields = ['creation_date', 'created_by']
    ordering = ('creation_date',)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        filter_data = {'organization': self.organization }
        return queryset.filter(**filter_data)

    def list(self, request, org_pk, *args, **kwargs):
        self.organization = get_object_or_404(
                OrganizationStructure.objects.using(settings.READONLY_DATABASE),
                pk=org_pk)
        user_is_allowed_on_organization(request.user, self.organization)
        query_total = self.get_queryset()
        queryset = self.filter_queryset(query_total)
        data = self.paginate_queryset(queryset)
        response = {'data': data, 'recordsTotal': query_total.count(),
                    'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}
        return Response(self.get_serializer(response).data)
