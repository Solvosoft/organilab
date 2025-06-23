from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djgentelella.objectmanagement import AuthAllPermBaseObjectManagement
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from laboratory.models import OrganizationStructure
from sga.api.filterset import HCategoryFilterSet
from sga.api.serializers import DangerCategorySerializer, \
    DangerCategoryActionsSerializer, DangerCategoryDataTableSerializer
from sga.models import HCodeCategory


class HCodeCategoryViewSet(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": DangerCategoryDataTableSerializer,
        "create": DangerCategoryActionsSerializer,
        "update": DangerCategoryActionsSerializer,
        "retrieve": None,
        "get_values_for_update": None,
        "detail_template": None,
    }
    perms = {
        "list": ["sga.view_hcodecategory"],
        "create": ["sga.add_hcodecategory"],
        "update": ["sga.change_hcodecategory"],
        "retrieve": [],
        "get_values_for_update": [],
        "detail_template": [],
    }

    permission_classes = ()

    queryset = HCodeCategory.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['name',"threshold","danger_category", "h_code__code", "h_code__description"]
    filterset_class = HCategoryFilterSet
    ordering_fields = ["id"]
    ordering = ("id",)
    organization = None
