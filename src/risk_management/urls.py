from django.conf.urls import url, include

from risk_management import views as zoneviews

urlpatterns = [
    url(r'riskzone/list', zoneviews.ListZone.as_view(), name='riskzone_list'),
    url(r'riskzone/create', zoneviews.ZoneCreate.as_view(), name='riskzone_create'),
    url(r'riskzone/(?P<pk>\d+)/update', zoneviews.ZoneEdit.as_view(), name='riskzone_update'),
    url(r'riskzone/(?P<pk>\d+)/delete', zoneviews.ZoneDelete.as_view(), name='riskzone_delete'),
]