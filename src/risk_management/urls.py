from django.urls import path

from risk_management import views as zoneviews
from risk_management import incidents
urlpatterns = [
    path('riskzone/list/', zoneviews.ListZone.as_view(), name='riskzone_list'),
    path('riskzone/create/', zoneviews.ZoneCreate.as_view(), name='riskzone_create'),
    path('riskzone/<int:pk>/detail/', zoneviews.ZoneDetail.as_view(), name='riskzone_detail'),
    path('riskzone/<int:pk>/update/', zoneviews.ZoneEdit.as_view(), name='riskzone_update'),
    path('riskzone/<int:pk>/delete/', zoneviews.ZoneDelete.as_view(), name='riskzone_delete'),

    path('incident/<int:lab_pk>/list/', incidents.IncidentReportList.as_view(), name='incident_list'),
    path('incident/<int:lab_pk>/create/', incidents.IncidentReportCreate.as_view(), name='incident_create'),
    path('incident/<int:lab_pk>/<int:pk>/update/', incidents.IncidentReportEdit.as_view(), name='incident_update'),
    path('incident/<int:lab_pk>/<int:pk>/detail/', incidents.IncidentReportDetail.as_view(), name='incident_detail'),
    path('incident/<int:lab_pk>/<int:pk>/delete/', incidents.IncidentReportDelete.as_view(), name='incident_delete'),
    path('incident/report/<int:lab_pk>/<int:pk>/', incidents.report_incidentreport, name='incident_report' )
]