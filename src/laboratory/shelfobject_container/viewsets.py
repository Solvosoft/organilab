from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from djgentelella.objectmanagement import AuthAllPermBaseObjectManagement
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination

from auth_and_perms.organization_utils import user_is_allowed_on_organization, \
    organization_can_change_laboratory
from . import serializers
from ..models import ShelfObject, OrganizationStructure, Laboratory
from ..utils import check_user_access_kwargs_org_lab


class ContainerManagementViewset(AuthAllPermBaseObjectManagement):
    serializer_class = {
        'list': serializers.ContainerDataTableSerializer,
    }
    perms = {
        'list': ['laboratory.view_shelfobject'],
        'create': [],
        'update': [],
        'retrieve': [],
        'get_values_for_update': []
    }
    queryset = ShelfObject.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['object__name', ]  # for the global search
    filterset_class = serializers.ContainerFilter
    ordering_fields = ['creation_date', 'created_by', 'status']
    ordering = ('-creation_date',)  # default order
    operation_type = ''

    def get_queryset(self):
        queryset=super().get_queryset()
        queryset=queryset.filter(shelf=self.shelf)
        return queryset

    def list(self, request, *args, **kwargs):
        self.shelf = kwargs['shelf']
        org_pk=kwargs['org_pk']
        lab_pk=kwargs['lab_pk']
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
        user_is_allowed_on_organization(request.user, organization)
        laboratory = get_object_or_404(
            Laboratory.objects.using(settings.READONLY_DATABASE),
            pk=lab_pk)
        organization_can_change_laboratory(laboratory, organization,
                                           raise_exec=True)

        if not check_user_access_kwargs_org_lab(org_pk, lab_pk, request.user):
            raise Http404()

        return super().list(request, *args, **kwargs)


