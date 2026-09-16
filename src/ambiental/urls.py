from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ambiental import views
from ambiental.api import viewsets

router = DefaultRouter()
router.register(
    "measurementpoint", viewsets.MeasurementPointViewSet, basename="api-measurementpoint"
)
router.register(
    "consumptionrecord", viewsets.ConsumptionRecordViewSet, basename="api-consumptionrecord"
)

urlpatterns = [
    path(
        "measurement_points/",
        views.measurementpoint_list,
        name="measurementpoint_list",
    ),
    path(
        "consumption/",
        views.consumptionrecord_list,
        name="consumptionrecord_list",
    ),
    path("api/", include(router.urls)),
]
