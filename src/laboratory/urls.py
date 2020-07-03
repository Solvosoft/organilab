'''
Created on 1/8/2016

@author: nashyra
'''

from django.conf.urls import url, include

from laboratory import views
from authentication import users
from laboratory.reservation import ShelfObjectReservation
from laboratory.search import SearchObject
from laboratory.sustance.views import create_edit_sustance, sustance_list, SustanceListJson, SubstanceDelete
from laboratory.views import furniture, reports, shelfs, objectfeature
from laboratory.views import labroom, shelfobject, laboratory, solutions, organizations
from laboratory.views.access import access_management, users_management, delete_user
from laboratory.views.laboratory import LaboratoryListView, LaboratoryDeleteView
from laboratory.views.objects import ObjectView

objviews = ObjectView()

urlpatterns = [

    url(r'^(?P<lab_pk>\d+)$', views.lab_index, name='labindex'),

    url(r'^(?P<pk>\d+)/edit$', laboratory.LaboratoryEdit.as_view(), name='laboratory_update'),
    url(r'^(?P<pk>\d+)/ajax/list$', laboratory.admin_users, name='laboratory_ajax_admins_users_list'),
    url(r'^(?P<pk>\d+)/ajax/create$', laboratory.get_create_admis_user, name='laboratory_ajax_get_create_admins_user'),
    url(r'^(?P<pk>\d+)/ajax/post_create$', laboratory.create_admins_user, name='laboratory_ajax_create_admins_user'),
    url(r'^(?P<pk>\d+)/ajax/(?P<pk_user>\d+)/delete$', laboratory.del_admins_user,
        name='laboratory_ajax_del_admins_users'),
    url(r'^select$', laboratory.SelectLaboratoryView.as_view(), name='select_lab'),
    url(r'^create_lab$', laboratory.CreateLaboratoryFormView.as_view(), name='create_lab'),
    # Tour steps
    url(r'^_ajax/get_tour_steps$', views.get_tour_steps, name='get_tour_steps'),
    url(r'^_ajax/get_tour_steps_furniture$', views.get_tour_steps_furniture, name='get_tour_steps_furniture'),
    url(r"reserve_object/(?P<modelpk>\d+)$", ShelfObjectReservation.as_view(), name="object_reservation")
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

    url(r'^create/(?P<labroom>\d+)$', furniture.FurnitureCreateView.as_view(),
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
    url(r'^shelf_objects$', reports.report_shelf_objects,
        name='reports_shelf_objects'),
    url(r'^limited_shelf_objects$', reports.report_limited_shelf_objects,
        name='reports_limited_shelf_objects'),
    url(r'^reactive_precursor_objects$', reports.report_reactive_precursor_objects,
        name='reports_reactive_precursor_objects'),
    # HTML reports
    url(r'^list/laboratory$', labroom.LaboratoryRoomReportView.as_view(),
        name='reports_laboratory'),
    url(r'^list/furniture$$', furniture.FurnitureReportView.as_view(),
        name='reports_furniture_detail'),
    url(r'^list/objects$', reports.ObjectList.as_view(),
        name='reports_objects_list'),
    url(r'^list/limited_shelf_objects$', reports.LimitedShelfObjectList.as_view(),
        name='reports_limited_shelf_objects_list'),
    url(r'^list/reactive_precursor_objects$', reports.ReactivePrecursorObjectList.as_view(),
        name='reactive_precursor_object_list')
]

lab_reports_organization_urls = [
    url(r'^organization$', reports.report_organization_building,
        name='reports_organization_building'),
    url(r'^list$', organizations.OrganizationReportView.as_view(),
        name='reports_organization'),
]

lab_features_urls = [
    url(r'^create$', objectfeature.FeatureCreateView.as_view(),
        name='object_feature_create'),
    url(r'^edit/(?P<pk>\d+)$', objectfeature.FeatureUpdateView.as_view(),
        name='object_feature_update'),
    url(r'^delete/(?P<pk>\d+)$', objectfeature.FeatureDeleteView.as_view(),
        name='object_feature_delete'),
]

solutions_urls = [
    url(r'^calculator$', solutions.SolutionCalculatorView.as_view(),
        name='solution_calculator'),
    url(r'^$', solutions.SolutionListView.as_view(), name='solution_list'),
    url(r'^(?P<pk>\d+)$', solutions.SolutionDetailView.as_view(),
        name='solution_detail')
]


reports_all_lab=[
    url(r'^reports/hcode$', laboratory.HCodeReports.as_view(), name='h_code_reports'),
    url(r'^reports/download/hcode$', reports.report_h_code, name='download_h_code_reports'),
]

sustance_urls = [
    url('sustance/edit/(?P<pk>\d+)?$', create_edit_sustance, name='sustance_manage'),
    url('sustance/delete/(?P<pk>\d+)?$', SubstanceDelete.as_view(), name='sustance_delete'),
    url('sustance/$', sustance_list, name='sustance_list'),
    url('sustance/json$', SustanceListJson.as_view(), name='sustance_list_json'),
]

organization_urls = [
    url('access_list$', access_management, name="access_list"),
    url('access_list/(?P<pk>\d+)/users$', users_management, name="users_management"),
    url('access_list/(?P<pk>\d+)/users/(?P<user_pk>\d+)?$', delete_user, name="delete_user"),
    url('access_list/(?P<pk>\d+)/users/add$', users.AddUser.as_view(), name="add_user"),
]

'''MULTILAB'''
urlpatterns += sustance_urls + organization_urls + [
    url(r'mylabs$', LaboratoryListView.as_view(), name="mylabs"),
    url(r'^lab/(?P<pk>\d+)/delete', LaboratoryDeleteView.as_view(), name="laboratory_delete"),
    url(r"^lab/(?P<lab_pk>\d+)?/search$", SearchObject.as_view(), name="search"),
    url(r'^lab/(?P<lab_pk>\d+)/rooms/', include(lab_rooms_urls)),
    url(r'^lab/(?P<lab_pk>\d+)/furniture/', include(lab_furniture_urls)),
    url(r'^lab/(?P<lab_pk>\d+)/objects/', include(objviews.get_urls())),
    url(r'^lab/(?P<lab_pk>\d+)/reports/', include(lab_reports_urls)),
    url(r'^lab/(?P<lab_pk>\d+)/shelfobject/', include(shelf_object_urls)),
    url(r'^lab/(?P<lab_pk>\d+)/shelf/', include(lab_shelf_urls)),
    url(r'^lab/(?P<lab_pk>\d+)/features/', include(lab_features_urls)),
    url(r'^lab/(?P<lab_pk>\d+)/solutions/', include(solutions_urls)),
    url(r'^lab/(?P<lab_pk>\d+)/organizations/reports/',
        include(lab_reports_organization_urls)),

] +reports_all_lab
