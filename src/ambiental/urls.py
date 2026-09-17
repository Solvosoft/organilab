from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ambiental import forms, views
from ambiental.api import viewsets

router = DefaultRouter()
router.register(
    "measurementpoint", viewsets.MeasurementPointViewSet, basename="api-measurementpoint"
)
router.register(
    "consumptionrecord", viewsets.ConsumptionRecordViewSet, basename="api-consumptionrecord"
)
router.register(
    "consumptionalert", viewsets.ConsumptionAlertViewSet, basename="api-consumptionalert"
)
router.register(
    "normalizationbase", viewsets.NormalizationBaseViewSet, basename="api-normalizationbase"
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
    path(
        "normalization_bases/",
        views.normalizationbase_list,
        name="normalizationbase_list",
    ),
    path(
        "reports/consumption_detail/",
        views.AmbientalReportView.as_view(report_name="report_consumption_detail"),
        name="report_consumption_detail",
    ),
    path(
        "reports/consumption_summary/",
        views.AmbientalReportView.as_view(report_name="report_consumption_summary"),
        name="report_consumption_summary",
    ),
    path(
        "reports/consumption_cost/",
        views.AmbientalReportView.as_view(report_name="report_consumption_cost"),
        name="report_consumption_cost",
    ),
    path(
        "reports/environmental_indicators/",
        views.AmbientalReportView.as_view(
            report_name="report_environmental_indicators", form_class=forms.IndicatorReportForm
        ),
        name="report_environmental_indicators",
    ),
    path(
        "reports/consumption_comparison/",
        views.AmbientalReportView.as_view(
            report_name="report_consumption_comparison", form_class=forms.ComparisonReportForm
        ),
        name="report_consumption_comparison",
    ),
    path("dashboard/", views.AmbientalDashboard.as_view(), name="ambiental_dashboard"),
    path("waste/", views.waste_list, name="waste_list"),
    path(
        "reports/waste_manifest/",
        views.AmbientalReportView.as_view(report_name="report_waste_manifest"),
        name="report_waste_manifest",
    ),
    path("alerts/", views.consumptionalert_list, name="consumptionalert_list"),
    path("api/", include(router.urls)),
]
