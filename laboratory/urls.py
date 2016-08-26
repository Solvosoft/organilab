from django.conf.urls import url
from django.urls import reverse_lazy
from laboratory.views import LaboratoryRoomListView, ObjectListView, FurnitureListView
from django.contrib.auth import views as auth_views
from laboratory.generic import ObjectDeleteFromShelf, \
    ObjectList, \
    LaboratoryRoomsList
from laboratory.ajax_view import list_furniture, list_shelf, list_shelfobject, ShelfObjectCreate, ShelfObjectDelete
from laboratory import views


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login$', auth_views.login, {
        'template_name': 'laboratory/login.html'}, name='login'),
    url(r'^logout$', auth_views.logout, {
        'next_page': reverse_lazy('laboratory:index')},
        name='logout'),
    url(r"^delete/(?P<pk>\d+)$",
        ObjectDeleteFromShelf.as_view(), name="object_Delete"),
    # url(r"^list$", ObjectList.as_view(), name='object-list')
    url(r"^listLaboratoryRooms$", LaboratoryRoomsList.as_view(),
        name='laboratoryRooms_list')
]

urlpatterns += [
    url(r"^furniture/list/$", list_furniture, name="list_furniture"),
    url(r"^shelf/list$", list_shelf, name="list_shelf"),
    url(r"^shelfObject/list$", list_shelfobject, name="list_shelfobject"),
    url(r"^shelfObject/create$", ShelfObjectCreate.as_view(),
        name="shelfobject_create"),
    url(r"^shelfObject/delete/(?P<pk>\d+)$",
        ShelfObjectDelete.as_view(), name="shelfobject_delete"),
]

# URLS Adolfo
urlpatterns += [
    url(r"^labs$", LaboratoryRoomListView.as_view(),
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
        name="report_summaryfurniture")
]
