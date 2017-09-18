'''
Created on 1/8/2016

@author: nashyra
'''
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from laboratory import views
from laboratory.reservation import ShelfObjectReservation
from laboratory.search import SearchObject
from laboratory.views import PermissionDeniedView
from laboratory.views import furniture, reports, shelfs, objectfeature
from laboratory.views import labroom, shelfobject, laboratory, solutions
from laboratory.views import access
from laboratory.views.objects import ObjectView

objviews = ObjectView()

urlpatterns = [
    url(r'^(?P<lab_pk>\d+)?$', views.index, name='index'),
    url(r'^(?P<pk>\d+)/edit$', laboratory.LaboratoryEdit.as_view(), name='laboratory_update'),
    url(r'^(?P<pk>\d+)/ajax/list$', laboratory.admin_users, name='laboratory_ajax_admins_users_list'),
    url(r'^(?P<pk>\d+)/ajax/create$', laboratory.get_create_admis_user, name='laboratory_ajax_get_create_admins_user'),
    url(r'^(?P<pk>\d+)/ajax/post_create$', laboratory.create_admins_user, name='laboratory_ajax_create_admins_user'),

    url(r'^(?P<pk>\d+)/ajax/(?P<pk_user>\d+)/delete$', laboratory.del_admins_user, name='laboratory_ajax_del_admins_users'),

    url(r'^accounts/login/$', auth_views.login, {'template_name': 'laboratory/login.html'}, name='login'),
    url(r'^accounts/logout/$', auth_views.logout, {
        'next_page': reverse_lazy('laboratory:index')},
        name='logout'),
    url(r'^select$', laboratory.SelectLaboratoryView.as_view(), name='select_lab'),
    url(r'^permission_denied$', PermissionDeniedView.as_view(),
        name='permission_denied'),
    url(r'^feedback$', views.FeedbackView.as_view(), name='feedback'),
    url(r'^_ajax/get_tour_steps$', views.get_tour_steps, name='get_tour_steps'),
    url(r"reserve_object/(?P<modelpk>\d+)$",
        ShelfObjectReservation.as_view(),
        name="object_reservation")
]

lab_shelf_urls = [
    url(r"^list$", shelfs.list_shelf, name="list_shelf"),
    url(r"^create$", shelfs.ShelfCreate.as_view(), name="shelf_create"),
    url(r"^delete/(?P<pk>\d+)/(?P<row>\d+)/(?P<col>\d+)$",
        shelfs.ShelfDelete, name="shelf_delete"),
    url(r'^edit/(?P<pk>\d+)/(?P<row>\d+)/(?P<col>\d+)$',
        shelfs.ShelfEdit.as_view(), name="shelf_edit")
]

lab_rooms_urls = [
    url(r'^$', labroom.LaboratoryRoomsList.as_view(), name='rooms_list'),
    url(r'^create$', labroom.LabroomCreate.as_view(), name='rooms_create'),
    url(r'^(?P<pk>\d+)/delete$', labroom.LaboratoryRoomDelete.as_view(),
        name='rooms_delete'),
    url(r'^(?P<pk>\d+)/edit$', labroom.LabroomUpdate.as_view(),
        name='rooms_update'),
]

lab_furniture_urls = [
    url(r'^$', furniture.list_furniture, name='furniture_list'),
    url(r'^create$', furniture.FurnitureCreateView.as_view(),
        name='furniture_create'),
    url(r'^edit/(?P<pk>\d+)$', furniture.FurnitureUpdateView.as_view(),
        name='furniture_update'),
    url(r'^delete/(?P<pk>\d+)$', furniture.FurnitureDelete.as_view(),
        name='furniture_delete'),
]

shelf_object_urls = [
    url(r"^list$", shelfobject.list_shelfobject,
        name="list_shelfobject"),
    url(r"^create$", shelfobject.ShelfObjectCreate.as_view(),
        name="shelfobject_create"),
    url(r"^delete/(?P<pk>\d+)$",
        shelfobject.ShelfObjectDelete.as_view(), name="shelfobject_delete"),
    url(r"^edit/(?P<pk>\d+)$",
        shelfobject.ShelfObjectEdit.as_view(), name="shelfobject_edit"),
    url(r"q/update/(?P<pk>\d+)$", shelfobject.ShelfObjectSearchUpdate.as_view(),
        name="shelfobject_searchupdate")
]

lab_reports_urls = [
    # PDF reports
    url(r'^laboratory$', reports.report_labroom_building,
        name='report_building'),
    url(r'^furniture$', reports.report_furniture,
        name='reports_furniture'),
    url(r'^objects$', reports.report_objects, name='reports_objects'),
    url(r'^shelf_objects$', reports.report_shelf_objects, name='reports_shelf_objects'),
    url(r'^limited_shelf_objects$', reports.report_limited_shelf_objects, name='reports_limited_shelf_objects'),
    url(r'^reactive_precursor_objects$', reports.report_reactive_precursor_objects,
        name='reports_reactive_precursor_objects'),
    # HTML reports
    url(r'^list/laboratory$', labroom.LaboratoryRoomReportView.as_view(),
        name='reports_laboratory'),
    url(r'^list/furniture$$', furniture.FurnitureReportView.as_view(),
        name='reports_furniture_detail'),
    url(r'^list/objects$', reports.ObjectList.as_view(), name='reports_objects_list'),
    url(r'^list/limited_shelf_objects$', reports.LimitedShelfObjectList.as_view(),
        name='reports_limited_shelf_objects_list'),
    url(r'^list/reactive_precursor_objects$', reports.ReactivePrecursorObjectList.as_view(),
        name='reactive_precursor_object_list')
]

lab_features_urls = [
    url(r'^create$', objectfeature.FeatureCreateView.as_view(), name='object_feature_create'),
    url(r'^edit/(?P<pk>\d+)$', objectfeature.FeatureUpdateView.as_view(), name='object_feature_update'),
    url(r'^delete/(?P<pk>\d+)$', objectfeature.FeatureDeleteView.as_view(), name='object_feature_delete'),
]

solutions_urls = [
    url(r'^calculator$', solutions.SolutionCalculatorView.as_view(), name='solution_calculator'),
    url(r'^$', solutions.SolutionListView.as_view(), name='solution_list'),
    url(r'^(?P<pk>\d+)$', solutions.SolutionDetailView.as_view(), name='solution_detail')
]

lab_access_urls = [
    url(r'^labadmins$', access.AccessListLabAdminsView.as_view(), name='access_list_lab_admins'),
    url(r'^laboratorists$', access.AccessListLaboratoritsView.as_view(), name='access_list_laboratorits'),
    url(r'^students$', access.AccessListStudentsView.as_view(), name='access_list_students'),
    url(r'^saveuser$', access.save_user, name='save_user'),
]


'''MULTILAB'''
urlpatterns += [
    url(r"^lab/(?P<lab_pk>\d+)?/search$", SearchObject.as_view(), name="search"),
    url(r'^lab/(?P<lab_pk>\d+)/rooms/', include(lab_rooms_urls)),
    url(r'^lab/(?P<lab_pk>\d+)/furniture/', include(lab_furniture_urls)),
    url(r'^lab/(?P<lab_pk>\d+)/objects/', include(objviews.get_urls())),
    url(r'^lab/(?P<lab_pk>\d+)/reports/', include(lab_reports_urls)),
    url(r'^lab/(?P<lab_pk>\d+)/shelfobject/', include(shelf_object_urls)),
    url(r'^lab/(?P<lab_pk>\d+)/shelf/', include(lab_shelf_urls)),
    url(r'^lab/(?P<lab_pk>\d+)/features/', include(lab_features_urls)),
    url(r'^lab/(?P<lab_pk>\d+)/solutions/', include(solutions_urls)),

    url(r'^lab/(?P<lab_pk>\d+)/access/', include(lab_access_urls)),
]
