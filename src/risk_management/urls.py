from django.conf.urls import url, include

from risk_management import views as zoneviews
from risk_management import  incidents
urlpatterns = [
    url(r'riskzone/list', zoneviews.ListZone.as_view(), name='riskzone_list'),
    url(r'riskzone/create', zoneviews.ZoneCreate.as_view(), name='riskzone_create'),
    url(r'riskzone/(?P<pk>\d+)/detail', zoneviews.ZoneDetail.as_view(), name='riskzone_detail'),
    url(r'riskzone/(?P<pk>\d+)/update', zoneviews.ZoneEdit.as_view(), name='riskzone_update'),
    url(r'riskzone/(?P<pk>\d+)/delete', zoneviews.ZoneDelete.as_view(), name='riskzone_delete'),
    url(r'incident/(?P<lab_pk>\d+)/list/', incidents.IncidentReportList.as_view(), name='incident_list'),
    url(r'incident/(?P<lab_pk>\d+)/create', incidents.IncidentReportCreate.as_view(), name='incident_create'),
    url(r'incident/(?P<lab_pk>\d+)/(?P<pk>\d+)/update', incidents.IncidentReportEdit.as_view(), name='incident_update'),
    url(r'incident/(?P<lab_pk>\d+)/(?P<pk>\d+)/detail', incidents.IncidentReportDetail.as_view(), name='incident_detail'),
    url(r'incident/(?P<lab_pk>\d+)/(?P<pk>\d+)/delete', incidents.IncidentReportDelete.as_view(), name='incident_delete'),
    url(r'incident/report/(?P<lab_pk>\d+)/(?P<pk>\d+)?', incidents.report_incidentreport, name='incident_report' )
]