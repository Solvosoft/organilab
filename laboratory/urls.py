'''
Created on 1/8/2016

@author: nashyra
'''
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from laboratory import views
from laboratory.ObjectViews import ObjectView
from laboratory.ajax_view import list_furniture, list_shelfobject, ShelfObjectCreate, ShelfObjectDelete
from laboratory.ajax_view import list_shelf, list_objectfeatures, \
    admin_list_shelf, ShelfObjectEdit
from laboratory.generic import ObjectDeleteFromShelf, \
    LaboratoryRoomsList
from laboratory.generic import ShelfCreate, ObjectCreate, LabroomCreate, \
    ShelfDelete, LaboratoryRoomDelete, ShelfEdit
from laboratory.laboratory_views import LaboratoryView
from laboratory.laboratory_views import SelectLaboratoryView
from laboratory.reservation import ShelfObjectReservation
from laboratory.search import SearchObject
from laboratory.views import LaboratoryRoomListView, ObjectListView, FurnitureListView, \
    FurnitureCreateView, FurnitureUpdateView, FurnitureDelete, ReactivePrecursorObjectList


objviews = ObjectView()
labviews = LaboratoryView()

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^accounts/login/$', auth_views.login, {
        'template_name': 'laboratory/login.html'}, name='login'),
    url(r'^accounts/logout/$', auth_views.logout, {
        'next_page': reverse_lazy('laboratory:index')},
        name='logout'),
    url(r"^search$", SearchObject.as_view(),
        name="search"),
    url(r'^select', SelectLaboratoryView.as_view(), name='select_lab')
]

urlpatterns += [
    url(r"^shelfObject/list$", list_shelfobject, name="list_shelfobject"),
    url(r"^shelfObject/create$", ShelfObjectCreate.as_view(),
        name="shelfobject_create"),
    url(r"^shelfObject/delete/(?P<pk>\d+)$",
        ShelfObjectDelete.as_view(), name="shelfobject_delete"),
    url(r"^shelfObject/edit/(?P<pk>\d+)$",
        ShelfObjectEdit.as_view(), name="shelfobject_edit"),
]

urlpatterns += [
    url(r"^object/create$", ObjectCreate.as_view(),
        name="object_create"),
    url(r"^objects$", ObjectListView.as_view(),
        name="object_list"),
    url(r"^object/delete/(?P<pk>\d+)$",
        ObjectDeleteFromShelf.as_view(), name="object_Delete"),
    url(r"^objectfeatures/list$", list_objectfeatures,
        name="objectfeatures_list"),
]

urlpatterns += [
    url(r"^reports/laboratory$", LaboratoryRoomListView.as_view(),
        name="laboratoryroom_list"),
    url(r"^report/building$", views.report_building,
        name="report_building"),
    url(r"^report/objects$", views.report_objects,
        name="report_objects"),
    url(r'^report/reactive_precursor_objects', views.report_reactive_precursor_objects,
        name='report_reactive_precursor_objects'),
    url(r"^report/furniture$", views.report_furniture,
        name="report_furniture"),
    url(r"^report/furniture_detail$", FurnitureListView.as_view(),
        name="furniture_list"),
]

urlpatterns += [
    url(r"^object/create$", ObjectCreate.as_view(),
        name="object_create"),
    url(r"^objects$", ObjectListView.as_view(),
        name="object_list"),
    url(r"^object/delete/(?P<pk>\d+)$",
        ObjectDeleteFromShelf.as_view(), name="object_Delete"),
    url(r"^objectfeatures/list$", list_objectfeatures,
        name="objectfeatures_list"),
]

urlpatterns += [
    url(r"^listLaboratoryRooms$", LaboratoryRoomsList.as_view(),
        name='laboratoryRooms_list'),
    url(r"^laboratoryroom/create$", LabroomCreate.as_view(),
        name="laboratoryroom_create"),
    url(r"^laboratoryroom/delete/(?P<pk>\d+)$",
        LaboratoryRoomDelete.as_view(),
        name="laboratoryroom_delete"),
    url(r"^objectfeatures/list$", list_objectfeatures,
        name="objectfeatures_list"),
    url(r"^search$", SearchObject.as_view(),
        name="search"),
    url(r"reserve_object/(?P<modelpk>\d+)$",
        ShelfObjectReservation.as_view(),
        name="object_reservation")
]

urlpatterns += [
    url(r"^furniture/list/$",
        list_furniture, name="list_furniture"),
    url(r"^furniture/create$", FurnitureCreateView.as_view(),
        name="furniture_create"),
    url(r"^furniture/edit/(?P<pk>\d+)$", FurnitureUpdateView.as_view(),
        name="furniture_update"),
    url(r"furniture/delete/(?P<pk>\d+)$", FurnitureDelete.as_view(),
        name="furniture_delete")
]

urlpatterns += [
    url(r"^shelf/list$", list_shelf, name="list_shelf"),
    url(r"^shelf/delete/(?P<pk>\d+)/(?P<row>\d+)/(?P<col>\d+)$",
        ShelfDelete, name="shelf_delete"),
    url(r"^adm/shelf/list$", admin_list_shelf,
        name="shelf_list"),
    url(r"^shelf/create$", ShelfCreate.as_view(),
        name="shelf_create"),
    url(r'^shelf/edit/(?P<pk>\d+)/(?P<row>\d+)/(?P<col>\d+)$',
        ShelfEdit.as_view(), name="shelf_edit")
]

'''MULTILAB'''

lab_rooms_urls = [
    url(r'^$', LaboratoryRoomsList.as_view(), name='laboratory_rooms_list'),
    url(r'^create$', LabroomCreate.as_view(), name='laboratory_rooms_create'),
    url(r'^(?P<pk>\d+)/delete$', LaboratoryRoomDelete.as_view(),
        name='laboratory_rooms_delete'),
]

lab_furniture_urls = [
    url(r'^$', list_furniture, name='laboratory_furniture_list'),
    url(r'^create$', FurnitureCreateView.as_view(),
        name='laboratory_furniture_create'),
    url(r'^edit/(?P<pk>\d+)$', FurnitureUpdateView.as_view(),
        name='laboratory_furniture_update'),
    url(r'^delete/(?P<pk>\d+)$', FurnitureDelete.as_view(),
        name='laboratory_furniture_delete'),
]


lab_reports_urls = [
    url(r'^lab$', LaboratoryRoomListView.as_view(),
        name='laboratory_reports_laboratory'),
    url(r'^building$', views.report_building,
        name='laboratory_reports_building'),
    url(r'^objects$', views.report_objects, name='laboratory_reports_objects'),
    url(r'^reactive_precursor_objects$', views.report_reactive_precursor_objects,
        name='laboratory_reports_reactive_precursor_objects'),
    url(r'^furniture$', views.report_furniture,
        name='laboratory_reports_furniture'),
    url(r'^furniture_detail$', FurnitureListView.as_view(),
        name='laboratory_reports_furniture_detail')
]

urlpatterns += [
    url(r'^laboratory/(?P<lab_pk>\d+)/reactive_precursor_objects', ReactivePrecursorObjectList.as_view(),
        name='reactive_precursor_object_list')
]

'''MULTILAB'''
urlpatterns += [
    url(r'^laboratory/', include(labviews.get_urls())),
    url(r'^laboratory/(?P<lab_pk>\d+)/rooms/', include(lab_rooms_urls)),
    url(r'^laboratory/(?P<lab_pk>\d+)/furniture/',
        include(lab_furniture_urls)),
    url(r'^laboratory/(?P<lab_pk>\d+)/objects/', include(objviews.get_urls())),
    url(r'^laboratory/(?P<lab_pk>\d+)/reports/', include(lab_reports_urls)),
]

urlpatterns += objviews.get_urls()
