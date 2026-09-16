from ambiental.api import filtersets, serializers
from ambiental.api.mixins import AmbientalViewSet
from ambiental.models import ConsumptionRecord, MeasurementPoint


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
