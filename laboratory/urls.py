'''
Created on 1/8/2016

@author: nashyra
'''
from __future__ import unicode_literals
from laboratory.generic import ShelfCreate, ObjectCreate, LabroomCreate,\
    ShelfDelete, LaboratoryRoomDelete
from laboratory.ajax_view import list_shelf, list_objectfeatures,\
    admin_list_shelf, ShelfObjectEdit
from django.conf.urls import url
from django.urls import reverse_lazy
from laboratory.views import LaboratoryRoomListView, ObjectListView, FurnitureListView,\
    FurnitureCreateView, FurnitureUpdateView, FurnitureDelete
from django.contrib.auth import views as auth_views
from laboratory.generic import ObjectDeleteFromShelf, \
    ObjectList, \
    LaboratoryRoomsList
from laboratory.ajax_view import list_furniture, list_shelf, list_shelfobject, ShelfObjectCreate, ShelfObjectDelete
from laboratory import views
from laboratory.search import SearchObject
from laboratory.ObjectViews import ObjectView

objviews = ObjectView()

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^accounts/login/$', auth_views.login, {
        'template_name': 'laboratory/login.html'}, name='login'),
    url(r'^accounts/logout/$', auth_views.logout, {
        'next_page': reverse_lazy('laboratory:index')},
        name='logout'),
    url(r"^delete/(?P<pk>\d+)$",
        ObjectDeleteFromShelf.as_view(), name="object_Delete"),
    # url(r"^list$", ObjectList.as_view(), name='object-list')
    url(r"^listLaboratoryRooms$", LaboratoryRoomsList.as_view(),
        name='laboratoryRooms_list')
]

# Natalia Ajax
urlpatterns += [
    url(r"^furniture/list/$",
        list_furniture, name="list_furniture"),
    url(r"^shelf/list$", list_shelf, name="list_shelf"),
    url(r"^shelfObject/list$", list_shelfobject, name="list_shelfobject"),
    url(r"^shelfObject/create$", ShelfObjectCreate.as_view(),
        name="shelfobject_create"),
    url(r"^shelfObject/delete/(?P<pk>\d+)$",
        ShelfObjectDelete.as_view(), name="shelfobject_delete"),
    url(r"^shelfObject/edit/(?P<pk>\d+)$",
        ShelfObjectEdit.as_view(), name="shelfobject_edit"),
    url(r"^shelf/delete/(?P<pk>\d+)/(?P<row>\d+)/(?P<col>\d+)$",
        ShelfDelete, name="shelf_delete")
]

# URLS Adolfo
urlpatterns += [
    url(r"^reports/laboratory$", LaboratoryRoomListView.as_view(),
        name="laboratoryroom_list"),
    url(r"^objects$", ObjectListView.as_view(),
        name="object_list"),
    url(r"^furniture$", FurnitureListView.as_view(),
        name="furniture_list"),
]

urlpatterns += [
    url(r"^report/building$", views.report_building,
        name="report_building"),
    url(r"^report/objects$", views.report_objects,
        name="report_objects"),
    url(r"^report/furniture$", views.report_furniture,
        name="report_furniture"),
    url(r"^report/summaryfurniture$", views.report_sumfurniture,
        name="report_summaryfurniture"),
    url(r"^furniture/create$", FurnitureCreateView.as_view(),
        name="furniture_create"),
    url(r"^furniture/edit/(?P<pk>\d+)$", FurnitureUpdateView.as_view(),
        name="furniture_update"),
    url(r"furniture/delete/(?P<pk>\d+)$", FurnitureDelete.as_view(),
        name="furniture_delete")
]

urlpatterns += [
    url(r"^adm/shelf/list$", admin_list_shelf,
        name="shelf_list"),
    url(r"^shelf/create$", ShelfCreate.as_view(),
        name="shelf_create")
]

urlpatterns += [
    url(r"^object/create$", ObjectCreate.as_view(),
        name="object_create"),
    url(r"^objectfeatures/list$", list_objectfeatures,
        name="objectfeatures_list"),

]

urlpatterns += [
    url(r"^laboratoryroom/create$", LabroomCreate.as_view(),
        name="laboratoryroom_create"),
    url(r"^laboratoryroom/delete/(?P<pk>\d+)$",
        LaboratoryRoomDelete.as_view(),
        name="laboratoryroom_delete"),
    url(r"^objectfeatures/list$", list_objectfeatures,
        name="objectfeatures_list"),
    url(r"^search$", SearchObject.as_view(),
        name="search"),
]

urlpatterns += objviews.get_urls()
