from django.contrib.admin.models import DELETION
from django.db.models import F
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import OrganizationStructure
from laboratory.utils import organilab_logentry
from . import serializers
from laboratory.api.filterset import SubstanceFilterSet
from organilab import settings
from sga.models import Substance
from django.utils.translation import gettext_lazy as _


class SubstanceViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.SubstanceDataTableSerializer
    queryset = Substance.objects.using(settings.READONLY_DATABASE)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["created_by", "comercial_name", "uipa_name"]
    filterset_class = SubstanceFilterSet
    ordering_fields = ["-creation_date", "comercial_name"]
    ordering = ("-creation_date", "comercial_name")

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .filter(organization=self.organization)
            .annotate(cas_id=F("substancecharacteristics__cas_id_number"))
        )
        return queryset

    def list(self, request, org_pk, *args, **kwargs):
        self.organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
        )
        user_is_allowed_on_organization(request.user, self.organization)
        queryset = self.get_queryset()
        total_records = queryset.count()
        queryset = self.filterset_class.filter_queryset(self, queryset)
        data = self.paginate_queryset(queryset)
        response = {
            "data": data,
            "recordsTotal": total_records,
            "recordsFiltered": queryset.count(),
            "draw": self.request.GET.get("draw", 1),
        }
        return Response(self.get_serializer(response).data)

    def destroy(self, request, org_pk, *args, **kwargs):
        self.organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
        )
        user_is_allowed_on_organization(request.user, self.organization)
        instance = self.get_object()
        self.perform_destroy(instance)
        return JsonResponse(
            data={"detail": _("Substance deleted successfully")},
            status=status.HTTP_202_ACCEPTED,
        )

    def perform_destroy(self, instance):
        organilab_logentry(
            self.request.user,
            instance,
            DELETION,
            "SGA Substance " + str(instance),
            relobj=[self.organization],
        )
        instance.delete()
