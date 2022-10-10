from django.urls import re_path

from risk_management import views as zoneviews
from risk_management import  incidents
urlpatterns = [
    re_path(r'riskzone/list', zoneviews.ListZone.as_view(), name='riskzone_list'),
    re_path(r'riskzone/create', zoneviews.ZoneCreate.as_view(), name='riskzone_create'),
    re_path(r'riskzone/(?P<pk>\d+)/detail', zoneviews.ZoneDetail.as_view(), name='riskzone_detail'),
    re_path(r'riskzone/(?P<pk>\d+)/update', zoneviews.ZoneEdit.as_view(), name='riskzone_update'),
    re_path(r'riskzone/(?P<pk>\d+)/delete', zoneviews.ZoneDelete.as_view(), name='riskzone_delete'),
    re_path(r'incident/(?P<lab_pk>\d+)/list/', incidents.IncidentReportList.as_view(), name='incident_list'),
    re_path(r'incident/(?P<lab_pk>\d+)/create', incidents.IncidentReportCreate.as_view(), name='incident_create'),
    re_path(r'incident/(?P<lab_pk>\d+)/(?P<pk>\d+)/update', incidents.IncidentReportEdit.as_view(), name='incident_update'),
    re_path(r'incident/(?P<lab_pk>\d+)/(?P<pk>\d+)/detail', incidents.IncidentReportDetail.as_view(), name='incident_detail'),
    re_path(r'incident/(?P<lab_pk>\d+)/(?P<pk>\d+)/delete', incidents.IncidentReportDelete.as_view(), name='incident_delete'),
    re_path(r'incident/report/(?P<lab_pk>\d+)/(?P<pk>\d+)?', incidents.report_incidentreport, name='incident_report' )
]