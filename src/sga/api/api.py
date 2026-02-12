from django_filters.rest_framework import DjangoFilterBackend
from djgentelella.objectmanagement import AuthAllPermBaseObjectManagement
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination

from sga.api.filterset import DangerSubstanceFilterSet
from sga.api.serializers import DangerSubstanceDataTableSerializer, \
    DangerSubstanceValidateSerializer, DangerSubstanceSerializer
from sga.models import DangerSubstance


class DangerSubstanceViewSet(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": DangerSubstanceDataTableSerializer,
        "create": DangerSubstanceValidateSerializer,
        "update": DangerSubstanceValidateSerializer,
        "destroy": DangerSubstanceSerializer,
    }
    perms = {
        "list": ["sga.view_dangersubstance"],
        "create": ["sga.add_dangersubstance"],
        "update": ["sga.change_dangersubstance"],
        "destroy": ["sga.delete_dangersubstance"],
    }
    queryset = DangerSubstance.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = DangerSubstanceFilterSet
    search_fields = ["cas_code", "name"]
    ordering_fields = ["cas_code", "name"]
    ordering = ("name",)

