'''
Created on 1/8/2016

@author: nashyra
'''
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from laboratory import views
from laboratory.ajax_view import list_objectfeatures
from laboratory.laboratory_views import LaboratoryView
from laboratory.laboratory_views import SelectLaboratoryView
from laboratory.reservation import ShelfObjectReservation
from laboratory.search import SearchObject
from laboratory.views import PermissionDeniedView
from laboratory.views import furniture, reports, shelfs
from laboratory.views import labroom, shelfobject
from laboratory.views.objects import ObjectView


objviews = ObjectView()
labviews = LaboratoryView()

urlpatterns = [
    url(r'^(?P<lab_pk>\d)?$', views.index, name='index'),
    url(r'^accounts/login/$', auth_views.login, {
        'template_name': 'laboratory/login.html'}, name='login'),
    url(r'^accounts/logout/$', auth_views.logout, {
        'next_page': reverse_lazy('laboratory:index')},
        name='logout'),
    url(r'^select$', SelectLaboratoryView.as_view(), name='select_lab'),
    url(r'^permission_denied$', PermissionDeniedView.as_view(),
        name='permission_denied')
]


urlpatterns += [
    url(r"^objectfeatures/list$", list_objectfeatures,
        name="objectfeatures_list"),
    url(r"reserve_object/(?P<modelpk>\d+)$",
        ShelfObjectReservation.as_view(),
        name="object_reservation")
]


'''MULTILAB'''

lab_shelf_urls = [
    url(r"^list$", shelfs.list_shelf, name="list_shelf"),
    url(r"^create$", shelfs.ShelfCreate.as_view(), name="shelf_create"),
    url(r"^delete/(?P<pk>\d+)/(?P<row>\d+)/(?P<col>\d+)$",
        shelfs.ShelfDelete, name="shelf_delete"),
    url(r'^edit/(?P<pk>\d+)/(?P<row>\d+)/(?P<col>\d+)$',
        shelfs.ShelfEdit.as_view(), name="shelf_edit"),
    url(r"^adm/list$", shelfs.admin_list_shelf,
        name="shelf_list"),
]

lab_rooms_urls = [  # ok
    url(r'^$', labroom.LaboratoryRoomsList.as_view(), name='rooms_list'),
    url(r'^create$', labroom.LabroomCreate.as_view(), name='rooms_create'),
    url(r'^(?P<pk>\d+)/delete$', labroom.LaboratoryRoomDelete.as_view(),
        name='rooms_delete'),
]

lab_furniture_urls = [  # ok
    url(r'^$', furniture.list_furniture, name='furniture_list'),
    url(r'^create$', furniture.FurnitureCreateView.as_view(),
        name='furniture_create'),
    url(r'^edit/(?P<pk>\d+)$', furniture.FurnitureUpdateView.as_view(),
        name='furniture_update'),
    url(r'^delete/(?P<pk>\d+)$', furniture.FurnitureDelete.as_view(),
        name='furniture_delete'),
]

shelf_object_urls = [  # ok
    url(r"^list$", shelfobject.list_shelfobject,
        name="list_shelfobject"),
    url(r"^create$", shelfobject.ShelfObjectCreate.as_view(),
        name="shelfobject_create"),
    url(r"^delete/(?P<pk>\d+)$",
        shelfobject.ShelfObjectDelete.as_view(), name="shelfobject_delete"),
    url(r"^edit/(?P<pk>\d+)$",
        shelfobject.ShelfObjectEdit.as_view(), name="shelfobject_edit"),
    url(r"q/update/(?P<pk>\d+)$$", shelfobject.ShelfObjectSearchUpdate.as_view(),
        name="shelfobject_searchupdate")
]


lab_reports_urls = [
    url(r'^laboratory$', labroom.LaboratoryRoomReportView.as_view(),
        name='reports_laboratory'),
    url(r'^building$', reports.report_labroom_building,
        name='report_building'),
    url(r'^objects$', reports.report_objects, name='reports_objects'),
    url(r'^reactive_precursor_objects$', reports.report_reactive_precursor_objects,
        name='reports_reactive_precursor_objects'),
    url(r'^furniture$', reports.report_furniture,
        name='reports_furniture'),
    url(r'^furniture/details$', furniture.FurnitureReportView.as_view(),
        name='reports_furniture_detail'),
    url(r'^list/reactive_precursor_objects$', reports.ReactivePrecursorObjectList.as_view(),
        name='reactive_precursor_object_list'),
    url(r'^list/objects$', reports.ObjectList.as_view(), name='reports_objects_list')
]


'''MULTILAB'''
urlpatterns += [
    #url(r'^lab/', include(labviews.get_urls())),
    url(r"^lab/(?P<lab_pk>\d+)?/search$", SearchObject.as_view(),
        name="search"),
    url(r'^lab/(?P<lab_pk>\d+)/rooms/', include(lab_rooms_urls)),
    url(r'^lab/(?P<lab_pk>\d+)/furniture/',
        include(lab_furniture_urls)),
    url(r'^lab/(?P<lab_pk>\d+)/objects/', include(objviews.get_urls())),
    url(r'^lab/(?P<lab_pk>\d+)/reports/', include(lab_reports_urls)),
    url(r'^lab/(?P<lab_pk>\d+)/shelfobject/', include(shelf_object_urls)),
    url(r'^lab/(?P<lab_pk>\d+)/shelf/', include(lab_shelf_urls))
]
