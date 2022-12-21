from django.urls import re_path

from risk_management import views as zoneviews
from risk_management import  incidents
urlpatterns = [
    re_path(r'riskzone/list/(?P<org_pk>\d+)', zoneviews.ListZone.as_view(), name='riskzone_list'),
    re_path(r'riskzone/create/(?P<org_pk>\d+)', zoneviews.ZoneCreate.as_view(), name='riskzone_create'),
    re_path(r'riskzone/(?P<pk>\d+)/detail/(?P<org_pk>\d+)', zoneviews.ZoneDetail.as_view(), name='riskzone_detail'),
    re_path(r'riskzone/(?P<pk>\d+)/update/(?P<org_pk>\d+)', zoneviews.ZoneEdit.as_view(), name='riskzone_update'),
    re_path(r'riskzone/(?P<pk>\d+)/delete/(?P<org_pk>\d+)', zoneviews.ZoneDelete.as_view(), name='riskzone_delete'),
    re_path(r'incident/(?P<lab_pk>\d+)/list/(?P<org_pk>\d+)', incidents.IncidentReportList.as_view(), name='incident_list'),
    re_path(r'incident/(?P<lab_pk>\d+)/create/(?P<org_pk>\d+)', incidents.IncidentReportCreate.as_view(), name='incident_create'),
    re_path(r'incident/(?P<lab_pk>\d+)/(?P<pk>\d+)/update/(?P<org_pk>\d+)', incidents.IncidentReportEdit.as_view(), name='incident_update'),
    re_path(r'incident/(?P<lab_pk>\d+)/(?P<pk>\d+)/detail/(?P<org_pk>\d+)', incidents.IncidentReportDetail.as_view(), name='incident_detail'),
    re_path(r'incident/(?P<lab_pk>\d+)/(?P<pk>\d+)/delete/(?P<org_pk>\d+)', incidents.IncidentReportDelete.as_view(), name='incident_delete'),
    re_path(r'incident/report/(?P<lab_pk>\d+)/(?P<pk>\d+)?', incidents.report_incidentreport, name='incident_report' )
]