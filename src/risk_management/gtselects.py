from django.shortcuts import get_object_or_404
from djgentelella.groute import register_lookups
from djgentelella.permission_management import AnyPermissionByAction
from djgentelella.views.select2autocomplete import BaseSelect2View
from requests import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication

from laboratory.gtselects import GPaginatorMoreElements
from laboratory.models import Laboratory
from risk_management.models import RiskZone, Buildings


@register_lookups(prefix="risk_laboratories", basename="risk_laboratories")
class RiskLaboraratory(BaseSelect2View):
    model = Laboratory
    fields = ['name']
    org= None
    risk = None
    authentication_classes = [SessionAuthentication]
    pagination_class = GPaginatorMoreElements
    perms = {
        'list': ["laboratory.view_laboratory"],
    }
    permission_classes = (AnyPermissionByAction,)
    def get_queryset(self):
        queryset = super().get_queryset()

        if self.org and self.risk:
            risk = get_object_or_404(RiskZone, pk=self.risk)
            queryset= queryset.filter(organization__pk=self.org,
                                      pk__in=risk.buildings.all().values_list("laboratories__pk", flat=True)).distinct()
        else:
            queryset= queryset.none()

        return queryset

    def list(self, request, *args, **kwargs):
        if self.request.GET.get("org_pk", None):
            self.org = self.request.GET.get("org_pk", None)
            self.risk = self.request.GET.get("risk", None)
            return super().list(request, *args, **kwargs)

        return Response({
            'status': 'Bad request',
            'errors': _("Organization not found"),
        }, status=status.HTTP_400_BAD_REQUEST)

@register_lookups(prefix="risk_buildings", basename="risk_buildings")
class RiskBuildings(BaseSelect2View):
    model = Buildings
    fields = ['name']
    org= None
    risk = None
    authentication_classes = [SessionAuthentication]
    pagination_class = GPaginatorMoreElements
    perms = {
        'list': ["risk_management.view_building"],
    }
    permission_classes = (AnyPermissionByAction,)
    def get_queryset(self):
        queryset = super().get_queryset()

        if self.org and self.risk:
            risk = get_object_or_404(RiskZone, pk=self.risk)
            queryset= queryset.filter(organization__pk=self.org,
                                      pk__in=risk.buildings.values_list("pk", flat=True)).distinct()
        else:
            queryset= queryset.none()

        return queryset

    def list(self, request, *args, **kwargs):
        if self.request.GET.get("org_pk", None):
            self.org = self.request.GET.get("org_pk", None)
            self.risk = self.request.GET.get("risk", None)
            return super().list(request, *args, **kwargs)

        return Response({
            'status': 'Bad request',
            'errors': _("Organization not found"),
        }, status=status.HTTP_400_BAD_REQUEST)


@register_lookups(prefix="regent_laboratories", basename="regent_laboratories")
class RegentLaboraratory(BaseSelect2View):
    model = Laboratory
    fields = ['name']
    org= None
    authentication_classes = [SessionAuthentication]
    pagination_class = GPaginatorMoreElements
    perms = {
        'list': ["laboratory.view_laboratory"],
    }
    permission_classes = (AnyPermissionByAction,)
    def get_queryset(self):
        queryset = super().get_queryset()

        if self.org:
            queryset= queryset.filter(organization__pk=self.org).distinct()
        else:
            queryset= queryset.none()

        return queryset

    def list(self, request, *args, **kwargs):
        if self.request.GET.get("org_pk", None):
            self.org = self.request.GET.get("org_pk", None)
            return super().list(request, *args, **kwargs)

        return Response({
            'status': 'Bad request',
            'errors': _("Organization not found"),
        }, status=status.HTTP_400_BAD_REQUEST)

