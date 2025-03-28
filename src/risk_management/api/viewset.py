from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djgentelella.objectmanagement import AuthAllPermBaseObjectManagement
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination

from laboratory.models import OrganizationStructure
from risk_management.api.serializer import RegentDataTableSerializer, \
    AddRegentSerializer, BuildingDataTableSerializer
from risk_management.models import Buildings, Regent


class RegentViewSet(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": RegentDataTableSerializer,
        "create": AddRegentSerializer,
        "update": None,
        "retrieve": None,
        "get_values_for_update": None,
        "detail_template": None,
    }
    perms = {
        "list": [],
        "create": [],
        "update": [],
        "retrieve": [],
        "get_values_for_update": [],
        "detail_template": [],
    }

    permission_classes = ()

    queryset = Regent.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["id"]
    filterset_class = None
    ordering_fields = ["id"]
    ordering = ("id",)
    organization = None
    def get_queryset(self):
        queryset = super().get_queryset()
        if "org_pk" in self.kwargs:
            org_pk = self.kwargs["org_pk"]
            queryset = queryset.filter(organization__pk=org_pk)

        return queryset

    def get_organization(self):
        if not hasattr(self, "_organization"):
            self.organization = get_object_or_404(
                OrganizationStructure, pk=self.kwargs.get("org_pk", None)
            )
        return self.organization

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["org_pk"] = self.kwargs.get("org_pk")
        return context

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user, organization=self.get_organization()
        )


class BuildingViewSet(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": BuildingDataTableSerializer,
        "create": None,
        "update": None,
        "retrieve": None,
        "get_values_for_update": None,
        "detail_template": None,
    }
    perms = {
        "list": [],
        "create": [],
        "update": [],
        "retrieve": [],
        "get_values_for_update": [],
        "detail_template": [],
    }

    permission_classes = ()

    queryset = Buildings.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["id"]
    filterset_class = None
    ordering_fields = ["id"]
    ordering = ("id",)
    organization = None
    def get_queryset(self):
        queryset = super().get_queryset()
        if "org_pk" in self.kwargs:
            org_pk = self.kwargs["org_pk"]
            queryset = queryset.filter(organization__pk=org_pk)

        return queryset

    def get_organization(self):
        if not hasattr(self, "_organization"):
            self.organization = get_object_or_404(
                OrganizationStructure, pk=self.kwargs.get("org_pk", None)
            )
        return self.organization

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["org_pk"] = self.kwargs.get("org_pk")
        return context

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user, organization=self.get_organization()
        )
