from django.urls import path, include
from rest_framework.routers import DefaultRouter

from laboratory.views.furniture import add_catalog
from risk_management import views as zoneviews
from risk_management import incidents
from risk_management import iper_views
from risk_management.api.viewset import (
    RegentViewSet,
    BuildingViewSet,
    StructureViewSet,
    IncidentViewSet,
    WorkdaysViewSet,
)

risk_router = DefaultRouter()
risk_router.register("api_regent", RegentViewSet, basename="api-regent")
building_router = DefaultRouter()
building_router.register("api_building", BuildingViewSet, basename="api-building")
structure_router = DefaultRouter()
structure_router.register("api_structure", StructureViewSet, basename="api-structure")

incident_router = DefaultRouter()
incident_router.register("api_incident", IncidentViewSet, basename="api-incident")
workday_router = DefaultRouter()
workday_router.register("api_workday", WorkdaysViewSet, basename="api-workday")

urlpatterns = [
    path("riskzone/list/", zoneviews.ListZone.as_view(), name="riskzone_list"),
    path("riskzone/create/", zoneviews.ZoneCreate.as_view(), name="riskzone_create"),
    path(
        "riskzone/<int:pk>/detail/",
        zoneviews.ZoneDetail.as_view(),
        name="riskzone_detail",
    ),
    path(
        "riskzone/<int:pk>/update/",
        zoneviews.ZoneEdit.as_view(),
        name="riskzone_update",
    ),
    path(
        "riskzone/<int:pk>/delete/",
        zoneviews.ZoneDelete.as_view(),
        name="riskzone_delete",
    ),
    path(
        "incident/<int:building_pk>/list/",
        incidents.IncidentReportList.as_view(),
        name="incident_list",
    ),
    path(
        "incident/<int:building_pk>/create/",
        incidents.IncidentReportCreate.as_view(),
        name="incident_create",
    ),
    path(
        "incident/<int:building_pk>/<int:pk>/update/",
        incidents.IncidentReportEdit.as_view(),
        name="incident_update",
    ),
    path(
        "incident/<int:building_pk>/<int:pk>/detail/",
        incidents.IncidentReportDetail.as_view(),
        name="incident_detail",
    ),
    path(
        "incident/<int:building_pk>/<int:pk>/delete/",
        incidents.IncidentReportDelete.as_view(),
        name="incident_delete",
    ),
    path(
        "incident/report/<int:risk_pk>/<int:pk>/",
        incidents.report_incidentreport,
        name="incident_report",
    ),
    path("zone_type/add/", zoneviews.add_zone_type_view, name="zone_type_add"),
    path("buildings/", zoneviews.buildings_view, name="buildings_list"),
    path("buildings/create/", zoneviews.buildings_actions, name="buildings_create"),
    path(
        "buildings/update/<int:pk>/",
        zoneviews.buildings_actions,
        name="buildings_update",
    ),
    path("regents/", zoneviews.regent_view, name="regents"),
    path("structures/", zoneviews.structure_view, name="structures_list"),
    path("structures/create/", zoneviews.structure_actions, name="structures_create"),
    path(
        "structures/update/<int:pk>/",
        zoneviews.structure_actions,
        name="structures_update",
    ),
    path("dashboard/", zoneviews.ZoneDashboard.as_view(), name="zone_dashboard"),
    path("api/risk/", include(risk_router.urls)),
    path("api/building/", include(building_router.urls)),
    path("api/structure/", include(structure_router.urls)),
    path("api/incident/<int:risk>/", include(incident_router.urls)),
    path("reports/", zoneviews.RiskZoneReport.as_view(), name="risk_report"),
    path(
        "workdays/<int:risk_zone>/",
        zoneviews.workday_view,
        name="workday_list",
    ),
    path(
        "api/workday/<int:risk>/",
        include(workday_router.urls),
        name="api-workday",
    ),
    # --- IPER (INTE T55) ---
    path("iper/list/", iper_views.IPERAssessmentList.as_view(), name="iper_list"),
    path("iper/create/", iper_views.IPERAssessmentCreate.as_view(), name="iper_create"),
    path(
        "iper/<int:pk>/detail/",
        iper_views.IPERAssessmentDetail.as_view(),
        name="iper_detail",
    ),
    path(
        "iper/<int:pk>/toggle-anonymous/",
        iper_views.iper_toggle_anonymous,
        name="iper_toggle_anonymous",
    ),
    path(
        "iper/<int:pk>/update/",
        iper_views.IPERAssessmentUpdate.as_view(),
        name="iper_update",
    ),
    path(
        "iper/<int:pk>/delete/",
        iper_views.IPERAssessmentDelete.as_view(),
        name="iper_delete",
    ),
    path(
        "iper/<int:pk>/clone/",
        iper_views.iper_clone_for_update,
        name="iper_clone",
    ),
    path(
        "iper/<int:pk>/observation/",
        iper_views.iper_observation_add,
        name="iper_observation_add",
    ),
    path(
        "iper/<int:assessment_pk>/hazard/create/",
        iper_views.iper_hazard_action,
        name="iper_hazard_create",
    ),
    path(
        "iper/<int:assessment_pk>/hazard/<int:pk>/update/",
        iper_views.iper_hazard_action,
        name="iper_hazard_update",
    ),
    path(
        "iper/<int:assessment_pk>/hazard/<int:pk>/delete/",
        iper_views.iper_hazard_delete,
        name="iper_hazard_delete",
    ),
    path("iper/history/", iper_views.IPERHistory.as_view(), name="iper_history"),
    path("iper/dashboard/", iper_views.IPERDashboard.as_view(), name="iper_dashboard"),
    path(
        "iper/zone/<int:risk_pk>/request/",
        iper_views.iper_request_for_zone,
        name="iper_request_zone",
    ),
    path(
        "iper/labdata/<int:lab_pk>/",
        iper_views.iper_lab_help,
        name="iper_lab_help",
    ),
    path("iper/catalog/add/", iper_views.iper_catalog_add, name="iper_catalog_add"),
]
