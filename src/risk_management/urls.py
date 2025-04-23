from django.urls import path, include
from rest_framework.routers import DefaultRouter

from laboratory.views.furniture import add_catalog
from risk_management import views as zoneviews
from risk_management import incidents
from risk_management.api.viewset import RegentViewSet, BuildingViewSet, \
    StructureViewSet, IncidentViewSet

risk_router = DefaultRouter()
risk_router.register(
    "api_regent", RegentViewSet, basename="api-regent"
)
building_router = DefaultRouter()
building_router.register(
    "api_building", BuildingViewSet, basename="api-building"
)
structure_router = DefaultRouter()
structure_router.register(
    "api_structure", StructureViewSet, basename="api-structure"
)
incident_router = DefaultRouter()
incident_router.register(
    "api_incident", IncidentViewSet, basename="api-incident"
)
urlpatterns = [
    path('riskzone/list/', zoneviews.ListZone.as_view(), name='riskzone_list'),
    path('riskzone/create/', zoneviews.ZoneCreate.as_view(), name='riskzone_create'),
    path('riskzone/<int:pk>/detail/', zoneviews.ZoneDetail.as_view(), name='riskzone_detail'),
    path('riskzone/<int:pk>/update/', zoneviews.ZoneEdit.as_view(), name='riskzone_update'),
    path('riskzone/<int:pk>/delete/', zoneviews.ZoneDelete.as_view(), name='riskzone_delete'),

    path('incident/<int:building_pk>/list/', incidents.IncidentReportList.as_view(), name='incident_list'),
    path('incident/<int:building_pk>/create/', incidents.IncidentReportCreate.as_view(), name='incident_create'),
    path('incident/<int:building_pk>/<int:pk>/update/', incidents.IncidentReportEdit.as_view(), name='incident_update'),
    path('incident/<int:building_pk>/<int:pk>/detail/', incidents.IncidentReportDetail.as_view(), name='incident_detail'),
    path('incident/<int:building_pk>/<int:pk>/delete/', incidents.IncidentReportDelete.as_view(), name='incident_delete'),
    path('incident/report/<int:building_pk>/<int:pk>/', incidents.report_incidentreport, name='incident_report' ),
    path('zone_type/add/', zoneviews.add_zone_type_view, name='zone_type_add'),
    path('buildings/', zoneviews.buildings_view, name='buildings_list'),
    path('buildings/create/', zoneviews.buildings_actions, name='buildings_create'),
    path('buildings/update/<int:pk>/', zoneviews.buildings_actions, name='buildings_update'),
    path('regents/', zoneviews.regent_view, name='regents'),
    path('structures/', zoneviews.structure_view, name='structures_list'),
    path('structures/create/', zoneviews.structure_actions, name='structures_create'),
    path('structures/update/<int:pk>/', zoneviews.structure_actions, name='structures_update'),
    path('api/risk/', include(risk_router.urls)),
    path('api/building/', include(building_router.urls)),
    path('api/structure/', include(structure_router.urls)),
    path('api/incident/<int:risk>/', include(incident_router.urls)),

]
