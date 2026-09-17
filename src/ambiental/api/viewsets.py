from django.contrib.admin.models import ADDITION, CHANGE
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from ambiental.api import filtersets, serializers
from ambiental.api.mixins import AmbientalViewSet
from ambiental.models import ConsumptionAlert, ConsumptionRecord, MeasurementPoint, NormalizationBase
from ambiental.normalization import preload_bases


class MeasurementPointViewSet(AmbientalViewSet):
    serializer_class = {
        "list": serializers.MeasurementPointDataTableSerializer,
        "create": serializers.MeasurementPointSaveSerializer,
        "update": serializers.MeasurementPointSaveSerializer,
        "retrieve": serializers.MeasurementPointSerializer,
        "get_values_for_update": serializers.MeasurementPointSerializer,
    }
    perms = {
        "list": ["ambiental.view_measurementpoint"],
        "create": ["ambiental.add_measurementpoint"],
        "update": ["ambiental.change_measurementpoint"],
        "retrieve": ["ambiental.view_measurementpoint"],
        "get_values_for_update": ["ambiental.change_measurementpoint"],
        "destroy": ["ambiental.delete_measurementpoint"],
    }
    queryset = MeasurementPoint.objects.select_related(
        "point_type", "resource_type", "building"
    ).prefetch_related("laboratories")
    search_fields = ["code", "name", "building__name", "resource_type__description"]
    filterset_class = filtersets.MeasurementPointFilter
    ordering_fields = ["code", "name", "building__name"]
    ordering = ("code",)

    def get_related_objects(self, instance):
        return [instance.building]


class ConsumptionRecordViewSet(AmbientalViewSet):
    serializer_class = {
        "list": serializers.ConsumptionRecordDataTableSerializer,
        "create": serializers.ConsumptionRecordSaveSerializer,
        "update": serializers.ConsumptionRecordSaveSerializer,
        "retrieve": serializers.ConsumptionRecordSerializer,
        "get_values_for_update": serializers.ConsumptionRecordSerializer,
    }
    perms = {
        "list": ["ambiental.view_consumptionrecord"],
        "create": ["ambiental.add_consumptionrecord"],
        "update": ["ambiental.change_consumptionrecord"],
        "retrieve": ["ambiental.view_consumptionrecord"],
        "get_values_for_update": ["ambiental.change_consumptionrecord"],
        "destroy": ["ambiental.delete_consumptionrecord"],
    }
    queryset = ConsumptionRecord.objects.select_related(
        "point__building", "point__resource_type", "unit", "treatment", "waste_manager"
    )
    search_fields = ["point__code", "point__name", "point__building__name", "note"]
    filterset_class = filtersets.ConsumptionRecordFilter
    ordering_fields = ["period_start", "period_end", "quantity", "total_cost"]
    ordering = ("-period_end",)

    def get_related_objects(self, instance):
        return [instance.point.building]


class NormalizationBaseViewSet(AmbientalViewSet):
    serializer_class = {
        "list": serializers.NormalizationBaseDataTableSerializer,
        "create": serializers.NormalizationBaseSaveSerializer,
        "update": serializers.NormalizationBaseSaveSerializer,
        "retrieve": serializers.NormalizationBaseSerializer,
        "get_values_for_update": serializers.NormalizationBaseSerializer,
        "preload": serializers.PreloadSerializer,
    }
    perms = {
        "list": ["ambiental.view_normalizationbase"],
        "create": ["ambiental.add_normalizationbase"],
        "update": ["ambiental.change_normalizationbase"],
        "retrieve": ["ambiental.view_normalizationbase"],
        "get_values_for_update": ["ambiental.change_normalizationbase"],
        "destroy": ["ambiental.delete_normalizationbase"],
        "preload": ["ambiental.preload_normalizationbase"],
    }
    queryset = NormalizationBase.objects.select_related("normalizer", "building")
    search_fields = ["building__name", "normalizer__description"]
    filterset_class = filtersets.NormalizationBaseFilter
    ordering_fields = ["year", "building__name", "value"]
    ordering = ("-year",)

    def get_related_objects(self, instance):
        return [instance.building]

    @action(detail=False, methods=["post"])
    def preload(self, request, org_pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = preload_bases(
            self.get_organization(), serializer.validated_data["year"], user=request.user
        )
        for base in result["created"]:
            self._add_log(base, ADDITION, [], _("Preloaded"))
        for base in result["updated"]:
            self._add_log(base, CHANGE, ["value"], _("Preloaded"))
        return Response(
            {
                "detail": _("%(created)d bases created, %(updated)d updated, %(skipped)d skipped.")
                % {
                    "created": len(result["created"]),
                    "updated": len(result["updated"]),
                    "skipped": result["skipped"],
                },
                "created": len(result["created"]),
                "updated": len(result["updated"]),
                "skipped": result["skipped"],
            },
            status=status.HTTP_200_OK,
        )


class ConsumptionAlertViewSet(AmbientalViewSet):
    serializer_class = {
        "list": serializers.ConsumptionAlertDataTableSerializer,
        "retrieve": serializers.ConsumptionAlertSerializer,
        "review": serializers.ReviewSerializer,
    }
    perms = {
        "list": ["ambiental.view_consumptionalert"],
        "retrieve": ["ambiental.view_consumptionalert"],
        "review": ["ambiental.review_consumptionalert"],
    }
    http_method_names = ["get", "post"]
    queryset = ConsumptionAlert.objects.select_related("point__building", "rule", "reviewed_by")
    search_fields = ["message", "point__code", "point__name", "point__building__name"]
    filterset_class = filtersets.ConsumptionAlertFilter
    ordering_fields = ["period", "variation_pct", "reviewed"]
    ordering = ("reviewed", "-variation_pct", "-period")

    def get_related_objects(self, instance):
        return [instance.point.building]

    @action(detail=True, methods=["post"])
    def review(self, request, org_pk=None, pk=None):
        alert = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        alert.reviewed = True
        alert.reviewed_note = serializer.validated_data["note"]
        alert.reviewed_by = request.user
        alert.reviewed_at = timezone.now()
        alert.save()
        self._add_log(alert, CHANGE, ["reviewed", "reviewed_note"], _("Reviewed"))
        return Response({"detail": _("The alert was marked as reviewed.")})
