from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djgentelella.objectmanagement import AuthAllPermBaseObjectManagement
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination

from laboratory.models import OrganizationStructure
from risk_management.api.filterseet import BuildingFilter, StructureFilter, \
    IncidentReportFilter, RegentFilter
from risk_management.api.serializer import RegentDataTableSerializer, \
    AddRegentSerializer, BuildingDataTableSerializer, StructureDataTableSerializer, \
    IncidentReportDataTableSerializer, ActionIncidentReportSerializer, \
    UpdateRegentSerializer
from risk_management.models import Buildings, Regent, Structure, RiskZone, \
    IncidentReport


class RegentViewSet(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": RegentDataTableSerializer,
        "create": AddRegentSerializer,
        "update": UpdateRegentSerializer,
        "retrieve": None,
        "get_values_for_update": None,
        "detail_template": None,
    }
    perms = {
        "list": ["risk_management.view_regent"],
        "create": ["risk_management.add_regent"],
        "update": ["risk_management.change_regent"],
        "retrieve": [],
        "get_values_for_update": [],
        "detail_template": [],
    }

    permission_classes = ()

    queryset = Regent.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["user__username", "laboratories__name"]
    filterset_class = RegentFilter
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

class IncidentViewSet(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": IncidentReportDataTableSerializer,
        "create": ActionIncidentReportSerializer,
        "update": ActionIncidentReportSerializer,
        "retrieve": None,
        "get_values_for_update": None,
        "detail_template": None,
    }
    perms = {
        "list": ["risk_management.view_incidentreport"],
        "create": ["risk_management.add_incidentreport"],
        "update": ["risk_management.change_incidentreport"],
        "retrieve": ["risk_management.view_incidentreport"],
        "get_values_for_update": ["risk_management.view_incidentreport"],
        "detail_template": ["risk_management.view_incidentreport"],
    }

    permission_classes = ()

    queryset = IncidentReport.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["id", "short_description", "laboratories__name",
                     "buildings__name"]
    filterset_class = IncidentReportFilter
    ordering_fields = ["id"]
    ordering = ("id",)
    organization = None
    risk_zone = None

    def get_queryset(self):
        queryset = super().get_queryset()
        if "risk" in self.kwargs:
            risk = self.kwargs["risk"]
            queryset = queryset.filter(risk_zone__pk=risk)

        return queryset

    def get_organization(self):
        if not hasattr(self, "_organization"):
            self.organization = get_object_or_404(
                OrganizationStructure, pk=self.kwargs.get("org_pk", None)
            )
        return self.organization

    def get_risk_zone(self):
        if not hasattr(self, "_risk_zone"):
            self.risk_zone = get_object_or_404(
                RiskZone, pk=self.kwargs.get("risk", None)
            )
        return self.risk_zone

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["org_pk"] = self.kwargs.get("org_pk")
        context["risk_pk"] = self.kwargs.get("risk")
        return context

    def perform_create(self, serializer):
        serializer.save(
            risk_zone=self.get_risk_zone(),
            created_by=self.request.user, organization=self.get_organization()
        )

