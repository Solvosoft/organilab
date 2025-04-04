from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djgentelella.objectmanagement import AuthAllPermBaseObjectManagement
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination

from laboratory.models import OrganizationStructure
from risk_management.api.filterseet import BuildingFilter, StructureFilter
from risk_management.api.serializer import RegentDataTableSerializer, \
    AddRegentSerializer, BuildingDataTableSerializer, StructureDataTableSerializer
from risk_management.models import Buildings, Regent, Structure


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
        "list": ["risk_management.view_regent"],
        "create": ["risk_management.add_regent"],
        "update": [],
        "retrieve": [],
        "get_values_for_update": [],
        "detail_template": [],
    }

    permission_classes = ()

    queryset = Regent.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["name"]
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
        "list": ["risk_management.view_building"],
        "create": ["risk_management.add_buildings"],
        "update": [],
        "retrieve": [],
        "get_values_for_update": [],
        "detail_template": [],
    }

    permission_classes = ()

    queryset = Buildings.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["id", "name", "manager__username", "regents__username",
                     "laboratories__name", "nearby_buildings__name"]
    filterset_class = BuildingFilter
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

class StructureViewSet(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": StructureDataTableSerializer,
        "create": None,
        "update": None,
        "retrieve": None,
        "get_values_for_update": None,
        "detail_template": None,
    }
    perms = {
        "list": ["risk_management.view_structure"],
        "create": ["risk_management.add_structure"],
        "destroy": ["risk_management.delete_structure"],
        "update": [],
        "retrieve": [],
        "get_values_for_update": [],
        "detail_template": [],
    }

    permission_classes = ()

    queryset = Structure.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["id", "name", "manager__username", "buildings__name",
                     "type_structure__description"]
    filterset_class = StructureFilter
    ordering_fields = ["id"]
    ordering = ("id",)

    def get_queryset(self):
        queryset = super().get_queryset()
        if "org_pk" in self.kwargs:
            org_pk = self.kwargs["org_pk"]
            queryset = queryset.filter(organization__pk=org_pk)

        return queryset
