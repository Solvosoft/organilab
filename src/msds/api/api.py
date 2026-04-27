from django.contrib.admin.models import CHANGE
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django_filters.rest_framework import DjangoFilterBackend
from djgentelella.objectmanagement import AuthAllPermBaseObjectManagement
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import SDSTraceability, OrganizationStructure
from laboratory.utils import organilab_logentry
from laboratory.views import logentry
from msds.api.filterset import SDSTraceabilityFilterSet
from msds.api.serializer import (
    SDSTraceabilityDataTableSerializer,
    SDSTraceabilityValidateSerializer,
    SustanceCharacteristicsSerializer,
)
from django.utils.translation import gettext as _


class SDSTraceabilityViewSet(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": SDSTraceabilityDataTableSerializer,
        "verify": SDSTraceabilityValidateSerializer,
        "create": None,
        "update": None,
        "destroy": None,
        "get_sustance_characteristics_info": SustanceCharacteristicsSerializer,
    }
    perms = {
        "list": ["laboratory.view_sdstraceability"],
        "verify": ["laboratory.change_sdstraceability"],
        "get_sustance_characteristics_info": ["laboratory.view_sdstraceability"],
    }
    queryset = SDSTraceability.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = SDSTraceabilityFilterSet
    search_fields = ["sustance_characteristics__substance__name", "source"]
    ordering_fields = ["source", "is_verified", "creation_date"]
    ordering = ("-creation_date",)

    @action(detail=False, methods=["post"])
    def verify(self, request, org_pk):
        self.organization = get_object_or_404(OrganizationStructure, pk=org_pk)
        user_is_allowed_on_organization(request.user, self.organization)
        sds = get_object_or_404(SDSTraceability, pk=self.request.data.get("id", 0))
        serializer = self.get_serializer(
            data=request.data,
            instance=sds,
        )
        if serializer.is_valid():
            sds = serializer.save()
            if sds.is_verified:
                sds.verified_by = request.user
                sds.verified_date = now().date()
            else:
                sds.verified_date = None
                sds.verified_by = None
            sds.save()
            organilab_logentry(
                request.user,
                sds,
                CHANGE,
                "sds",
                ["is_verified", "verified_by", "verified_date"],
                change_message=(
                    _("Verify SDS") if sds.is_verified else _("Unverify SDS")
                ),
            )
            return Response(
                {
                    "detail": (
                        _("The verification was performed successfully.")
                        if sds.is_verified
                        else _("The unverification was performed successfully.")
                    )
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"detail": _("The SDS doesn't exist.")}, status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=["get"])
    def get_sustance_characteristics_info(self, request, org_pk):
        self.organization = get_object_or_404(OrganizationStructure, pk=org_pk)
        user_is_allowed_on_organization(request.user, self.organization)
        sds = get_object_or_404(SDSTraceability, pk=request.query_params.get("pk", 0))

        if not sds.sustance_characteristics:
            return Response(
                {"detail": _("No substance characteristics found.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SustanceCharacteristicsSerializer(sds.sustance_characteristics)
        return Response(serializer.data, status=status.HTTP_200_OK)
