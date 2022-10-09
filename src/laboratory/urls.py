'''
Created on 1/8/2016

@author: nashyra
'''

from django.conf.urls import include
from django.urls import path, re_path
from authentication.users import ChangeUser, password_change
from laboratory import views
from authentication import users
from laboratory.reservation import ShelfObjectReservation
from laboratory.search import SearchObject
from laboratory.sustance.views import create_edit_sustance, sustance_list, SustanceListJson, SubstanceDelete
from laboratory.views import furniture, reports, shelfs, objectfeature
from laboratory.views import labroom, shelfobject, laboratory, organizations
from laboratory.views.access import access_management, users_management, delete_user, edit_management
from laboratory.views.laboratory import LaboratoryListView, LaboratoryDeleteView, LaboratoryEdit
from laboratory.views.profiles_management import ProfilesListView,ProfileUpdateView
from laboratory.views.objects import ObjectView, block_notifications 
from laboratory.api.views import ApiReservedProductsCRUD, ApiReservationCRUD
from laboratory.views.my_reservations import MyReservationView
from laboratory.views.provider import ProviderCreate,ProviderList,ProviderUpdate
from laboratory.validators import validate_duplicate_initial_date
from laboratory.functions import return_laboratory_of_shelf_id
objviews = ObjectView()

urlpatterns = [
    re_path(r'rp/api/reservedProducts/(?P<pk>\d+)/', ApiReservedProductsCRUD.as_view(), name='api_reservation_detail'),
    path('rp/api/reservedProducts', ApiReservedProductsCRUD.as_view(), name='api_reservation_create'),
    re_path(r'rp/api/reservedProducts/(?P<pk>\d+)/delete/', ApiReservedProductsCRUD.as_view(), name='api_reservation_delete'),
    re_path(r'rp/api/reservedProducts/(?P<pk>\d+)/update/', ApiReservedProductsCRUD.as_view(), name='api_reservation_update'),
    re_path(r'r/api/reservation$', ApiReservationCRUD.as_view(), name='api_individual_reservation_create'),
    re_path(r"my_reservations/(?P<pk>\d+)$", MyReservationView.as_view(), name="my_reservations"),
    re_path(r'^(?P<lab_pk>\d+)$', views.lab_index, name='labindex'),
    re_path(r'^(?P<pk>\d+)/edit$', laboratory.LaboratoryEdit.as_view(), name='laboratory_update'),
    re_path(r'^select$', laboratory.SelectLaboratoryView.as_view(), name='select_lab'),
    re_path(r'^create_lab$', laboratory.CreateLaboratoryFormView.as_view(), name='create_lab'),
    # Tour steps
    re_path(r'^_ajax/get_tour_steps$', views.get_tour_steps, name='get_tour_steps'),
    re_path(r'^_ajax/get_tour_steps_furniture$', views.get_tour_steps_furniture, name='get_tour_steps_furniture'),
    re_path(r"reserve_object/(?P<modelpk>\d+)$", ShelfObjectReservation.as_view(), name="object_reservation"),

    re_path(r"validators", validate_duplicate_initial_date, name="date_validator"),
    re_path(r"returnLabId", return_laboratory_of_shelf_id, name="get_lab_id"),
]

lab_shelf_urls = [
    re_path(r"^list$", shelfs.list_shelf, name="list_shelf"),
    re_path(r"^create$", shelfs.ShelfCreate.as_view(), name="shelf_create"),
    re_path(r"^delete/(?P<pk>\d+)/(?P<row>\d+)/(?P<col>\d+)$",
        shelfs.ShelfDelete, name="shelf_delete"),
    re_path(r'^edit/(?P<pk>\d+)/(?P<row>\d+)/(?P<col>\d+)$',
        shelfs.ShelfEdit.as_view(), name="shelf_edit")
]

lab_rooms_urls = [
    re_path(r'^$', labroom.LaboratoryRoomsList.as_view(), name='rooms_list'),
    re_path(r'^create$', labroom.LabroomCreate.as_view(), name='rooms_create'),
    re_path(r'^(?P<pk>\d+)/delete$', labroom.LaboratoryRoomDelete.as_view(),
        name='rooms_delete'),
    re_path(r'^(?P<pk>\d+)/edit$', labroom.LabroomUpdate.as_view(),
        name='rooms_update'),
]

lab_furniture_urls = [
    re_path(r'^$', furniture.list_furniture, name='furniture_list'),

    re_path(r'^create/(?P<labroom>\d+)$', furniture.FurnitureCreateView.as_view(),
        name='furniture_create'),

    re_path(r'^edit/(?P<pk>\d+)$', furniture.FurnitureUpdateView.as_view(),
        name='furniture_update'),
    re_path(r'^delete/(?P<pk>\d+)$', furniture.FurnitureDelete.as_view(),
        name='furniture_delete'),
]

shelf_object_urls = [
    re_path(r"^list$", shelfobject.list_shelfobject,
        name="list_shelfobject"),
    re_path(r"^create$", shelfobject.ShelfObjectCreate.as_view(),
        name="shelfobject_create"),
    re_path(r"^delete/(?P<pk>\d+)$",
        shelfobject.ShelfObjectDelete.as_view(), name="shelfobject_delete"),
    re_path(r"^edit/(?P<pk>\d+)$",
        shelfobject.ShelfObjectEdit.as_view(), name="shelfobject_edit"),
    re_path(r"q/update/(?P<pk>\d+)$", shelfobject.ShelfObjectSearchUpdate.as_view(),
        name="shelfobject_searchupdate"),
    re_path(r"transfer_objects$", shelfobject.ListTransferObjects.as_view(), name="transfer_objects"),
]

lab_reports_urls = [
    # PDF reports
    re_path(r'^laboratory$', reports.report_labroom_building,
        name='report_building'),
    re_path(r'^furniture$', reports.report_furniture,
        name='reports_furniture'),
    re_path(r'^objects$', reports.report_objects, name='reports_objects'),
    re_path(r'^shelf_objects$', reports.report_shelf_objects,
        name='reports_shelf_objects'),
    re_path(r'^limited_shelf_objects$', reports.report_limited_shelf_objects,
        name='reports_limited_shelf_objects'),
    re_path(r'^reactive_precursor_objects$', reports.report_reactive_precursor_objects,
        name='reports_reactive_precursor_objects'),
    # HTML reports
    re_path(r'^list/laboratory$', labroom.LaboratoryRoomReportView.as_view(),
        name='reports_laboratory'),
    re_path(r'^list/furniture$$', furniture.FurnitureReportView.as_view(),
        name='reports_furniture_detail'),
    re_path(r'^list/objects$', reports.ObjectList.as_view(),
        name='reports_objects_list'),
    re_path(r'^list/limited_shelf_objects$', reports.LimitedShelfObjectList.as_view(),
        name='reports_limited_shelf_objects_list'),
    re_path(r'^list/reactive_precursor_objects$', reports.ReactivePrecursorObjectList.as_view(),
        name='reactive_precursor_object_list'),
    re_path('^objectchanges$', reports.LogObjectView.as_view(), name='object_change_logs'),
    re_path('^precursors$', reports.PrecursorsView.as_view(), name='precursor_report'),
    re_path('^organizationreactivepresence/$', reports.OrganizationReactivePresenceList.as_view(), name='organizationreactivepresence'),

]

lab_reports_organization_urls = [
    re_path(r'^organization$', reports.report_organization_building,
        name='reports_organization_building'),
    re_path(r'^list$', organizations.OrganizationReportView.as_view(),
        name='reports_organization'),
]

lab_features_urls = [
    re_path(r'^create$', objectfeature.FeatureCreateView.as_view(),
        name='object_feature_create'),
    re_path(r'^edit/(?P<pk>\d+)$', objectfeature.FeatureUpdateView.as_view(),
        name='object_feature_update'),
    re_path(r'^delete/(?P<pk>\d+)$', objectfeature.FeatureDeleteView.as_view(),
        name='object_feature_delete'),
]

edit_objects=[
    re_path(r"^edit_object/(?P<pk>\d+)$", shelfobject.add_object,
        name="edit_object"),
    re_path(r"^get_object_detail", shelfobject.send_detail,
        name="get_object_detail"),
    re_path(r"update_transfer/(?P<pk>\d+)$", shelfobject.objects_transfer, name="update_transfer"),
    re_path(r"shelfs_list$", shelfobject.get_shelf_list, name="get_shelfs"),
    re_path(r"delete_transfer(?P<pk>\d+)$", shelfobject.delete_transfer, name="delete_transfer"),

]
reports_all_lab=[
    re_path(r'^reports/hcode$', laboratory.HCodeReports.as_view(), name='h_code_reports'),
    re_path(r'^reports/download/hcode$', reports.report_h_code, name='download_h_code_reports'),
]

sustance_urls = [
    re_path('sustance/edit/(?P<pk>\d+)?/(?P<lab_pk>\d+)?$', create_edit_sustance, name='sustance_manage'),
    re_path('sustance/add/(?P<lab_pk>\d+)?$', create_edit_sustance, name='sustance_add'),
    re_path('sustance/delete/(?P<pk>\d+)/lab/(?P<lab_pk>\d+)?$', SubstanceDelete.as_view(), name='sustance_delete'),
    re_path('sustance/(?P<lab_pk>\d+)$', sustance_list, name='sustance_list'),
    re_path('sustance/json/(?P<pk>\d+)?$', SustanceListJson.as_view(), name='sustance_list_json'),
]

organization_urls = [
    re_path('access_list$', access_management, name="access_list"),
    re_path('access_list/(?P<pk>\d+)/users$', users_management, name="users_management"),
    re_path('access_list/(?P<pk>\d+)/users/(?P<user_pk>\d+)?$', delete_user, name="delete_user"),
    re_path('access_list/(?P<pk>\d+)/users/add$', users.AddUser.as_view(), name="add_user"),
    re_path('profile/(?P<pk>\d+)/info$', ChangeUser.as_view(), name='profile'),
    re_path('profile/(?P<pk>\d+)/password$', password_change, name='password_change'),
    re_path('access_list/edit$', edit_management, name="edit_organization"),

]

lab_profiles_urls = [
    re_path(r"list$", ProfilesListView.as_view(), name="lab_profiles"),
    re_path(r"DEBUG_TOOLBARlist/(?P<pk>\d+)/(?P<profile_pk>\d+)$", ProfileUpdateView.as_view(), name="update_lab_profile"),
] 

provider_urls=[
    re_path(r"provider$", ProviderCreate.as_view(), name="add_provider"),
    re_path(r"update_provider/(?P<pk>\d+)$", ProviderUpdate.as_view(), name="update_lab_provider"),
    re_path(r"list$", ProviderList.as_view(), name="list_provider"),
]
'''MULTILAB'''
urlpatterns += sustance_urls + organization_urls + [
    re_path(r'mylabs$', LaboratoryListView.as_view(), name="mylabs"),
    re_path(r'^lab/(?P<pk>\d+)/edit', LaboratoryEdit.as_view(), name="laboratory_edit"),
    re_path(r'^lab/(?P<pk>\d+)/delete', LaboratoryDeleteView.as_view(), name="laboratory_delete"),
    re_path(r"^lab/(?P<lab_pk>\d+)?/search$", SearchObject.as_view(), name="search"),
    re_path(r'^lab/(?P<lab_pk>\d+)/rooms/', include(lab_rooms_urls)),
    re_path(r'^lab/(?P<lab_pk>\d+)/furniture/', include(lab_furniture_urls)),
    re_path(r'^lab/(?P<lab_pk>\d+)/objects/', include(objviews.get_urls())),
    re_path(r'^lab/(?P<lab_pk>\d+)/reports/', include(lab_reports_urls)),
    re_path(r'^lab/(?P<lab_pk>\d+)/shelfobject/', include(shelf_object_urls)),
    re_path(r'^lab/(?P<lab_pk>\d+)/shelf/', include(lab_shelf_urls)),
    re_path(r'^lab/(?P<lab_pk>\d+)/features/', include(lab_features_urls)),
    re_path(r'^lab/(?P<lab_pk>\d+)/organizations/reports/',
        include(lab_reports_organization_urls)),
    re_path(r'^lab/(?P<lab_pk>\d+)?/profiles/',include(lab_profiles_urls)),
    re_path(r'^lab/(?P<lab_pk>\d+)?/',include(provider_urls)),
    path(
        'lab/<int:lab_pk>/blocknotifications/<int:obj_pk>/', 
        block_notifications, name="block_notification") 
] +reports_all_lab+edit_objects
