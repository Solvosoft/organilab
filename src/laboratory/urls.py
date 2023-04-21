'''
Created on 1/8/2016
'''

from django.conf.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from academic.api.views import ReviewSubstanceViewSet
from authentication.users import ChangeUser, password_change, get_profile
from laboratory import views
from laboratory.api.views import ApiReservedProductsCRUD, ApiReservationCRUD, CommentAPI, ProtocolViewSet, \
    LogEntryViewSet, InformViewSet, ShelfObjectAPI, ShelfObjectGraphicAPI, ShelfList, ShelfObjectViewSet
from laboratory.functions import return_laboratory_of_shelf_id
from laboratory.protocol.views import protocol_list, ProtocolCreateView, ProtocolDeleteView, ProtocolUpdateView
from laboratory.reservation import ShelfObjectReservation
from laboratory.search import SearchObject, SearchDisposalObject
from laboratory.sustance.views import create_edit_sustance, sustance_list, SustanceListJson, SubstanceDelete
from laboratory.validators import validate_duplicate_initial_date
from laboratory.views import furniture, reports, shelfs, objectfeature
from laboratory.views import inform_period
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
    path('my_reservations/<int:lab_pk>', MyReservationView.as_view(), name="my_reservations"),
    path('labindex/<int:lab_pk>', views.lab_index, name='labindex'),
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
    path('reserve_object/<int:modelpk>', ShelfObjectReservation.as_view(), name="object_reservation"),
    path('validators', validate_duplicate_initial_date, name="date_validator"),
    path('returnLabId', return_laboratory_of_shelf_id, name="get_lab_id"),
]

lab_shelf_urls = [
    #path('list/<int:furniture_pk>', shelfs.list_shelf, name="list_shelf"),
    path('create/', shelfs.ShelfCreate.as_view(), name="shelf_create"),
    path('delete/<int:pk>/<int:row>/<int:col>/', shelfs.ShelfDelete, name="shelf_delete"),
    path('edit/<int:pk>/<int:row>/<int:col>/', shelfs.ShelfEdit.as_view(), name="shelf_edit")

]

lab_rooms_urls = [
    path('', labroom.LaboratoryRoomsList.as_view(), name='rooms_list'),
    path('create', labroom.LabroomCreate.as_view(), name='rooms_create'),
    path('rebuild_laboratory_qr', labroom.rebuild_laboratory_qr, name='rebuild_laboratory_qr'),
    path('<int:pk>/delete', labroom.LaboratoryRoomDelete.as_view(), name='rooms_delete'),
    path('<int:pk>/edit', labroom.LabroomUpdate.as_view(), name='rooms_update'),
]

lab_furniture_urls = [
    path('', furniture.list_furniture, name='furniture_list'),
    path('create/<int:labroom>/', furniture.FurnitureCreateView.as_view(), name='furniture_create'),
    path('edit/<int:pk>/', furniture.FurnitureUpdateView.as_view(), name='furniture_update'),
    path('delete/<int:pk>/', furniture.FurnitureDelete.as_view(), name='furniture_delete'),
]

shelf_object_urls = [
    path('list/', shelfobject.list_shelfobject, name="list_shelfobject"),
    path('create/', shelfobject.ShelfObjectCreate.as_view(), name="shelfobject_create"),
    path('delete/<int:pk>/', shelfobject.ShelfObjectDelete.as_view(), name="shelfobject_delete"),
    path('detail/<int:pk>/', shelfobject.ShelfObjectDetail.as_view(), name="shelfobject_detail"),
    path('edit/<int:pk>/', shelfobject.ShelfObjectEdit.as_view(), name="shelfobject_edit"),
    path('q/update/<int:pk>/', shelfobject.ShelfObjectSearchUpdate.as_view(), name="shelfobject_searchupdate"),
    path('transfer_objects/', shelfobject.ListTransferObjects.as_view(), name="transfer_objects"),
    path('get_shelfobject_limit/<int:pk>/', shelfobject.edit_limit_object, name="get_shelfobject_limit"),
    path('download_shelfobject_qr/<int:pk>/', shelfobject.download_shelfobject_qr, name="download_shelfobject_qr"),
]

lab_reports_urls = [
    # PDF reports
    path('laboratory/', reports.report_labroom_building, name='report_building'),
    path('furniture/', reports.report_furniture,  name='reports_furniture'),
    path('objects/', reports.report_objects, name='reports_objects'),
    path('shelf_objects/<int:pk>', reports.report_shelf_objects, name='reports_shelf_objects'),
    path('limited_shelf_objects/', reports.report_limited_shelf_objects,
         name='reports_limited_shelf_objects'),
    path('reactive_precursor_objects/', reports.report_reactive_precursor_objects,
         name='reports_reactive_precursor_objects'),
    # HTML reports
    path('list/laboratory/', labroom.LaboratoryRoomReportView.as_view(),
         name='reports_laboratory'),
    path('list/furniture/', furniture.FurnitureReportView.as_view(),
         name='reports_furniture_detail'),
    path('list/objects/', reports.ObjectList.as_view(),
         name='reports_objects_list'),
    path('list/limited_shelf_objects/', reports.LimitedShelfObjectList.as_view(),
         name='reports_limited_shelf_objects_list'),
    path('list/reactive_precursor_objects/', reports.ReactivePrecursorObjectList.as_view(),
         name='reactive_precursor_object_list'),
    path('objectchanges/', reports.LogObjectView.as_view(), name='object_change_logs'),
    path('precursors/', reports.PrecursorsView.as_view(), name='precursor_report'),

]

lab_reports_organization_urls = [
    path('organization', reports.report_organization_building,
         name='reports_organization_building'),
    path('list', organizations.OrganizationReportView.as_view(),
         name='reports_organization'),

]

lab_features_urls = [
    path('create/', objectfeature.FeatureCreateView.as_view(),
         name='object_feature_create'),
    path('edit/<int:pk>/', objectfeature.FeatureUpdateView.as_view(),
         name='object_feature_update'),
    path('delete/<int:pk>/', objectfeature.FeatureDeleteView.as_view(),
         name='object_feature_delete'),
]

edit_objects = [
    path('edit_object/<int:pk>/', shelfobject.add_object,  name="edit_object"),
    path('get_object_detail', shelfobject.send_detail, name="get_object_detail"),
    path('update_transfer/<int:org_pk>/<int:lab_pk>/<int:transfer_pk>/<int:shelf_pk>', shelfobject.objects_transfer, name="update_transfer"),
    path('shelfs_list/', shelfobject.get_shelf_list, name="get_shelfs"),
    path('delete_transfer/<int:pk>/', shelfobject.delete_transfer, name="delete_transfer"),

]

reports_all_lab = [
    path('reports/hcode', laboratory.HCodeReports.as_view(), name='h_code_reports'),
    path('reports/download/hcode', reports.report_h_code, name='download_h_code_reports'),
    path('organizationreactivepresence/', reports.OrganizationReactivePresenceList.as_view(),
         name='organizationreactivepresence'),
]

sustance_urls = [
    path('', sustance_list, name='sustance_list'),
    path('add/', create_edit_sustance, name='sustance_add'),
    path('edit/<int:pk>/', create_edit_sustance, name='sustance_manage'),
    path('delete/<int:pk>/', SubstanceDelete.as_view(), name='sustance_delete'),
    path('json/', SustanceListJson.as_view(), name='sustance_list_json'),
]

organization_urls = [
    path('organization/<int:pk>/delete', OrganizationDeleteView.as_view(), name="delete_organization"),
    path('organization/create', OrganizationCreateView.as_view(), name="create_organization"),
    path('organization/<int:pk>/update', OrganizationUpdateView.as_view(), name="update_organization"),
    path('profile/<int:pk>/info', ChangeUser.as_view(), name='profile'),
    path('profile/<int:pk>/password', password_change, name='password_change'),
    path('profile/info/<int:org_pk>/<int:pk>', get_profile, name='profile_detail'),
    path('logentry/<int:org_pk>', get_logentry_from_organization, name='logentry_list'),
    path('reports/<int:org_pk>/', reports.report_index, name='reports'),
]

provider_urls = [
    path('provider/', ProviderCreate.as_view(), name="add_provider"),
    path('update_provider/<int:pk>/', ProviderUpdate.as_view(), name="update_lab_provider"),
    path('list/', ProviderList.as_view(), name="list_provider"),
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

catalogs_urls = [
    path('furniture/furniture_type', furniture.add_catalog,kwargs={'key': "furniture_type"}, name='add_furniture_type_catalog'),
    path('shelf/container_type', furniture.add_catalog, kwargs={'key': 'container_type'}, name='add_shelf_type_catalog'),
]

informs_period_urls=[
    path('index/', inform_period.get_inform_index, name="inform_index" ),
    path('add/', inform_period.InformSchedulerAdd.as_view(), name="add_period_scheduler" ),
    path('edit/<int:pk>/', inform_period.InformSchedulerEdit.as_view(), name="edit_period_scheduler" ),
    path('detail/<int:pk>/', inform_period.InformSchedulerDetail.as_view(), name="detail_period_scheduler" ),

]

user_register_qr = [
    path('list/', laboratory.RegisterUserQRList.as_view(), name="list_register_user_qr"),
    path('manage/<int:pk>/', laboratory.manage_register_qr, name="manage_register_user_qr"),
    path('delete/<int:pk>/', laboratory.RegisterUserQRDeleteView.as_view(), name="delete_register_user_qr"),
    path('download/<int:pk>/', laboratory.get_pdf_register_user_qr, name="download_register_user_qr"),
    path('logentry/<int:pk>/', laboratory.get_logentry_from_registeruserqr, name='logentry_register_user_qr'),
    path('login/<int:pk>/', laboratory.login_register_user_qr, name='login_register_user_qr'),
    path('create_user_qr/<int:pk>/<int:user>', laboratory.create_user_qr, name='create_user_qr'),
    path('redirect_user_to_labindex/<int:pk>/', laboratory.redirect_user_to_labindex, name='redirect_user_to_labindex'),
]

"""APIS"""
router = DefaultRouter()

router.register('api_inform', CommentAPI, basename='api-inform')
router.register('api_protocol', ProtocolViewSet, basename='api-protocol')
router.register('api_logentry', LogEntryViewSet, basename='api-logentry')
router.register('api_reviewsubstance', ReviewSubstanceViewSet, basename='api-reviewsubstance')
router.register('api_informs', InformViewSet, basename='api-informs')
router.register('api_shelfobject', ShelfObjectViewSet, basename='api-shelfobject')
'''MULTILAB'''
urlpatterns += organization_urls + [
    path('<int:org_pk>/', include(organization_urls_org_pk)),
    path('inform_manager/<int:org_pk>/', include(informs_period_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/protocols/', include(lab_protocols_urls)),
    path('lab/<int:org_pk>/<int:pk>/delete/', LaboratoryDeleteView.as_view(), name="laboratory_delete"),
    path('lab/<int:org_pk>/<int:lab_pk>/search/', SearchObject.as_view(), name="search"),
    path('lab/<int:org_pk>/search/disposal/', SearchDisposalObject.as_view(), name="disposal_substance"),
    path('lab/<int:org_pk>/<int:lab_pk>/rooms/', include(lab_rooms_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/furniture/', include(lab_furniture_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/objects/', include(objviews.get_urls())),
    path('lab/<int:org_pk>/<int:lab_pk>/reports/', include(lab_reports_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/shelfobject/', include(shelf_object_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/shelf/', include(lab_shelf_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/features/', include(lab_features_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/organizations/reports/', include(lab_reports_organization_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/provider/', include(provider_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/informs/', include(informs_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/sustance/', include(sustance_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/blocknotifications/', block_notifications, name="block_notification"),
    path('org/<int:org_pk>/api/shelfobject/',  ShelfObjectAPI.as_view(), name='api_shelfobject'),
    path('org/api/shelfobject/graphic',  ShelfObjectGraphicAPI.as_view(), name='api_shelfobject_graphic'),
    path('org/api/shels/list',  ShelfList.as_view(), name='get_shelfs_list'),
    path('<int:org_pk>/', include(reports_all_lab)),
    path('catalogs/', include(catalogs_urls)),
    path('inform/api/', include(router.urls)),
    path('register_user_qr/<int:org_pk>/<int:lab_pk>/', include(user_register_qr)),

]  + edit_objects