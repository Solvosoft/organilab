from rest_framework.routers import DefaultRouter
from django.urls import path, include

from report.api.views import ReportDataViewSet, ReportDataLogViewSet, RegencyViewSet
from report.views import base
from report.views import reports_org

base_reports = [
    path("create/", base.create_request_by_report, name="create_report_request"),
    path(
        "create/",
        base.create_organization_request_by_report,
        name="create_organization_report_request",
    ),
    path("download/", base.download_report, name="generate_report"),
    path(
        "download/",
        base.download__organization_report,
        name="generate_organization_report",
    ),
    path("table/<int:pk>/", base.report_table, name="report_table"),
    path("status/", base.report_status, name="report_status"),
]
base_organization_reports = [
    path(
        "create/organization/",
        base.create_organization_request_by_report,
        name="create_organization_report_request",
    ),
    path(
        "download/organization/",
        base.download__organization_report,
        name="generate_organization_report",
    ),
    path(
        "table/organization/<int:pk>/",
        base.report_organization_table,
        name="report_organization_table",
    ),
    path("status/", base.report_status, name="report_organization_status"),
]

router = DefaultRouter()
router.register("api_report", ReportDataViewSet, basename="api-report")
router.register("api_report_log", ReportDataLogViewSet, basename="api-report-log")

router_report = DefaultRouter()
router_report.register("api_regency", RegencyViewSet, basename="api-regency")

app_name = "report"

report_urls = [
    path("regency/", base.regency_report, name="regency_report"),
    path(
        "list/furniture/",
        reports_org.FurnitureReportView.as_view(),
        name="reports_furniture_detail",
    ),
    path(
        "list/objects/", reports_org.ObjectList.as_view(), name="reports_objects_list"
    ),
    path(
        "list/limited_shelf_objects/",
        reports_org.LimitedShelfObjectList.as_view(),
        name="reports_limited_shelf_objects_list",
    ),
    path(
        "list/reactive_precursor_objects/",
        reports_org.ReactivePrecursorObjectList.as_view(),
        name="reactive_precursor_object_list",
    ),
    path(
        "objectchanges/",
        reports_org.LogObjectView.as_view(),
        name="object_change_logs",
    ),
    path("precursors/", reports_org.PrecursorsView.as_view(), name="precursor_report"),
    path(
        "list/waste/report",
        reports_org.DiscardShelfReportView.as_view(),
        name="waste_report",
    ),
    path(
        "list/reactive/report",
        reports_org.ReactiveReport.as_view(),
        name="reactive_report",
    ),
    path("risk_zone/", reports_org.RiskZoneReport.as_view(), name="risk_zone_report"),
    path(
        "reactive/stock/",
        reports_org.ReactiveStockReport.as_view(),
        name="reactive_stock_report",
    ),
]

urlpatterns = [
    path("api/", include(router.urls)),
    path("<int:org_pk>/", include(base_reports)),
    path("<int:org_pk>/", include(base_organization_reports)),
    path("reports/<int:org_pk>", include(report_urls)),
    path("api/reports/<int:org_pk>/", include(router_report.urls)),
]
