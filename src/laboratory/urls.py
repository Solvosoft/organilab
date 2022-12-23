'''
Created on 1/8/2016
'''

from django.conf.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from authentication.users import ChangeUser, password_change
from laboratory import views
from laboratory.api.views import ApiReservedProductsCRUD, ApiReservationCRUD, CommentAPI, ProtocolViewSet, \
    LogEntryViewSet
from laboratory.functions import return_laboratory_of_shelf_id
from laboratory.protocol.views import protocol_list, ProtocolCreateView, ProtocolDeleteView, ProtocolUpdateView
from laboratory.reservation import ShelfObjectReservation
from laboratory.search import SearchObject
from laboratory.sustance.views import create_edit_sustance, sustance_list, SustanceListJson, SubstanceDelete
from laboratory.validators import validate_duplicate_initial_date
from laboratory.views import furniture, reports, shelfs, objectfeature
from laboratory.views import labroom, shelfobject, laboratory, organizations
from laboratory.views.informs import get_informs, create_informs, complete_inform, remove_inform
from laboratory.views.laboratory import LaboratoryListView, LaboratoryDeleteView
from laboratory.views.logentry import get_logentry_from_organization
from laboratory.views.my_reservations import MyReservationView
from laboratory.views.objects import ObjectView, block_notifications
from laboratory.views.organizations import OrganizationDeleteView, OrganizationCreateView, OrganizationUpdateView
from laboratory.views.provider import ProviderCreate, ProviderList, ProviderUpdate

objviews = ObjectView()

organization_urls_org_pk = [
    path('my_reservations/<int:pk>', MyReservationView.as_view(), name="my_reservations"),
    path('labindex/<int:lab_pk>', views.lab_index, name='labindex'),  # Todo: remove this ?
    path('laboratory/<int:pk>/edit/', laboratory.LaboratoryEdit.as_view(), name='laboratory_update'),
    path('create_lab/', laboratory.CreateLaboratoryFormView.as_view(), name='create_lab'),
    path('my_labs/', LaboratoryListView.as_view(), name="mylabs"),
]

urlpatterns = [
    path('rp/api/reservedProducts/<int:pk>/', ApiReservedProductsCRUD.as_view(), name='api_reservation_detail'),
    path('rp/api/reservedProducts', ApiReservedProductsCRUD.as_view(), name='api_reservation_create'),
    path('rp/api/reservedProducts/<int:pk>/delete/', ApiReservedProductsCRUD.as_view(), name='api_reservation_delete'),
    path('rp/api/reservedProducts/<int:pk>/update/', ApiReservedProductsCRUD.as_view(), name='api_reservation_update'),
    path('r/api/reservation/', ApiReservationCRUD.as_view(), name='api_individual_reservation_create'),
    path('select', laboratory.SelectLaboratoryView.as_view(), name='select_lab'),
    path('reserve_object/<int:modelpk>', ShelfObjectReservation.as_view(), name="object_reservation"),
    path('validators', validate_duplicate_initial_date, name="date_validator"),
    path('returnLabId', return_laboratory_of_shelf_id, name="get_lab_id"),
]

lab_shelf_urls = [
    path('list/', shelfs.list_shelf, name="list_shelf"),
    path('create/', shelfs.ShelfCreate.as_view(), name="shelf_create"),
    path('delete/<int:pk>/<int:row>/<int:col>/', shelfs.ShelfDelete, name="shelf_delete"),
    path('edit/<int:pk>/<int:row>/<int:col>/', shelfs.ShelfEdit.as_view(), name="shelf_edit")
]

lab_rooms_urls = [
    path('', labroom.LaboratoryRoomsList.as_view(), name='rooms_list'),
    path('create', labroom.LabroomCreate.as_view(), name='rooms_create'),
    path('<int:pk>/delete', labroom.LaboratoryRoomDelete.as_view(), name='rooms_delete'),
    path('<int:pk>/edit', labroom.LabroomUpdate.as_view(), name='rooms_update'),
]

lab_furniture_urls = [
    path('', furniture.list_furniture, name='furniture_list'),
    path('create/<int:labroom>/<int:org_pk>/', furniture.FurnitureCreateView.as_view(), name='furniture_create'),
    path('edit/<int:pk>/<int:org_pk>/', furniture.FurnitureUpdateView.as_view(), name='furniture_update'),
    path('delete/<int:pk>/<int:org_pk>/', furniture.FurnitureDelete.as_view(), name='furniture_delete'),
]

shelf_object_urls = [
    path('list/', shelfobject.list_shelfobject, name="list_shelfobject"),
    path('create/', shelfobject.ShelfObjectCreate.as_view(), name="shelfobject_create"),
    path('delete/<int:pk>/', shelfobject.ShelfObjectDelete.as_view(), name="shelfobject_delete"),
    path('edit/<int:pk>/', shelfobject.ShelfObjectEdit.as_view(), name="shelfobject_edit"),
    path('q/update/<int:pk>/', shelfobject.ShelfObjectSearchUpdate.as_view(), name="shelfobject_searchupdate"),
    path('transfer_objects/', shelfobject.ListTransferObjects.as_view(), name="transfer_objects"),
    path('get_shelfobject_limit/<int:pk>/', shelfobject.edit_limit_object, name="get_shelfobject_limit"),
]

lab_reports_urls = [
    # PDF reports
    path('laboratory/', reports.report_labroom_building, name='report_building'),
    path('furniture/', reports.report_furniture,  name='reports_furniture'),
    path('objects/', reports.report_objects, name='reports_objects'),
    path('shelf_objects/', reports.report_shelf_objects, name='reports_shelf_objects'),
    path('limited_shelf_objects/', reports.report_limited_shelf_objects,
         name='reports_limited_shelf_objects'),
    path('reactive_precursor_objects/', reports.report_reactive_precursor_objects,
         name='reports_reactive_precursor_objects'),
    # HTML reports
    path('list/laboratory/', labroom.LaboratoryRoomReportView.as_view(),
         name='reports_laboratory'),
    path('list/furniture$/', furniture.FurnitureReportView.as_view(),
         name='reports_furniture_detail'),
    path('list/objects/', reports.ObjectList.as_view(),
         name='reports_objects_list'),
    path('list/limited_shelf_objects/', reports.LimitedShelfObjectList.as_view(),
         name='reports_limited_shelf_objects_list'),
    path('list/reactive_precursor_objects/', reports.ReactivePrecursorObjectList.as_view(),
         name='reactive_precursor_object_list'),
    path('objectchanges/', reports.LogObjectView.as_view(), name='object_change_logs'),
    path('precursors/', reports.PrecursorsView.as_view(), name='precursor_report'),
    path('organizationreactivepresence/', reports.OrganizationReactivePresenceList.as_view(),
         name='organizationreactivepresence'),

]

lab_reports_organization_urls = [
    path('organization', reports.report_organization_building,
         name='reports_organization_building'),
    path('list', organizations.OrganizationReportView.as_view(),
         name='reports_organization'),

]

lab_features_urls = [
    path('create/<int:org_pk>/', objectfeature.FeatureCreateView.as_view(),
         name='object_feature_create'),
    path('edit/<int:pk>/<int:org_pk>/', objectfeature.FeatureUpdateView.as_view(),
         name='object_feature_update'),
    path('delete/<int:pk>/<int:org_pk>/', objectfeature.FeatureDeleteView.as_view(),
         name='object_feature_delete'),
]

edit_objects = [
    path('edit_object/<int:pk>/', shelfobject.add_object,  name="edit_object"),
    path('get_object_detail', shelfobject.send_detail, name="get_object_detail"),
    path('update_transfer/<int:pk>/', shelfobject.objects_transfer, name="update_transfer"),
    path('shelfs_list/', shelfobject.get_shelf_list, name="get_shelfs"),
    path('delete_transfer/<int:pk>/', shelfobject.delete_transfer, name="delete_transfer"),

]
reports_all_lab = [
    path('reports/hcode', laboratory.HCodeReports.as_view(), name='h_code_reports'),
    path('reports/download/hcode', reports.report_h_code, name='download_h_code_reports'),
]

sustance_urls = [
    path('sustance/edit/<int:pk>/<int:lab_pk>/<int:org_pk>/', create_edit_sustance, name='sustance_manage'),
    path('sustance/add/<int:lab_pk>/<int:org_pk>/', create_edit_sustance, name='sustance_add'),
    path('sustance/delete/<int:pk>/lab/<int:lab_pk>/<int:org_pk>/', SubstanceDelete.as_view(), name='sustance_delete'),
    path('sustance/<int:lab_pk>/<int:org_pk>/', sustance_list, name='sustance_list'),
    path('sustance/json/<int:pk>/<int:org_pk>/', SustanceListJson.as_view(), name='sustance_list_json'),
]

organization_urls = [
    path('organization/<int:pk>/delete', OrganizationDeleteView.as_view(), name="delete_organization"),
    path('organization/create', OrganizationCreateView.as_view(), name="create_organization"),
    path('organization/<int:pk>/update', OrganizationUpdateView.as_view(), name="update_organization"),
    path('profile/<int:pk>/info', ChangeUser.as_view(), name='profile'),
    path('profile/<int:pk>/password', password_change, name='password_change'),
    path('logentry/<int:org_pk>', get_logentry_from_organization, name='logentry_list'),
    path('reports/<org_pk>/', reports.report_index, name='reports'),
]

provider_urls = [
    path('provider/<int:org_pk>/', ProviderCreate.as_view(), name="add_provider"),
    path('update_provider/<int:pk>/<int:org_pk>/', ProviderUpdate.as_view(), name="update_lab_provider"),
    path('list/<int:org_pk>/', ProviderList.as_view(), name="list_provider"),
]
informs_urls = [
    path('get_list/', get_informs, name="get_informs"),
    path('add_informs/<str:content_type>/<str:model>/', create_informs, name="add_informs"),
    path('complete_inform/<int:pk>/', complete_inform, name="complete_inform"),
    path('remove_inform/<int:pk>/', remove_inform, name="remove_inform"),
]
lab_protocols_urls = [
    path('list', protocol_list, name='protocol_list'),
    path('create', ProtocolCreateView.as_view(), name='protocol_create'),
    path('update/<int:pk>/', ProtocolUpdateView.as_view(), name='protocol_update'),
    path('delete/<int:pk>/', ProtocolDeleteView.as_view(), name='protocol_delete'),

    # path('regulations/', regulation_view, name="regulation_docs"),
    # path('regulations/download/all', download_all_regulations, name="download_all_regulations")
]

"""APIS"""
router = DefaultRouter()

router.register('api_inform', CommentAPI, basename='api-inform')
router.register('api_protocol', ProtocolViewSet, basename='api-protocol')
router.register('api_logentry', LogEntryViewSet, basename='api-logentry')

'''MULTILAB'''
urlpatterns += sustance_urls + organization_urls + [
    path('<int:org_pk>/', include(organization_urls_org_pk)),
    path('lab/<int:lab_pk>/protocols/', include(lab_protocols_urls)),
    path('lab/<int:pk>/delete/<int:org_pk>', LaboratoryDeleteView.as_view(), name="laboratory_delete"),
    path('lab/<int:lab_pk>/<int:org_pk>/search/', SearchObject.as_view(), name="search"),
    path('lab/<int:lab_pk>/<int:org_pk>/rooms/', include(lab_rooms_urls)),
    path('lab/<int:lab_pk>/furniture/', include(lab_furniture_urls)),
    path('lab/<int:lab_pk>/objects/', include(objviews.get_urls())),
    path('lab/<int:lab_pk>/reports/', include(lab_reports_urls)),
    path('lab/<int:lab_pk>/shelfobject/<int:org_pk>', include(shelf_object_urls)),
    path('lab/<int:lab_pk>/shelf/<int:org_pk>', include(lab_shelf_urls)),
    path('lab/<int:lab_pk>/features/', include(lab_features_urls)),
    path('lab//organizations/reports/', include(lab_reports_organization_urls)),
    path('lab/<int:lab_pk>?/provider/', include(provider_urls)),
    path('lab/<int:lab_pk>/informs/<int:org_pk>/', include(informs_urls)),
    path('inform/api/', include(router.urls)),
    path('lab/<int:lab_pk>/blocknotifications/<int:obj_pk>/', block_notifications, name="block_notification"),
    path('lab_reports_org/<int:obj_pk>/', include(lab_reports_organization_urls))

] + reports_all_lab + edit_objects
