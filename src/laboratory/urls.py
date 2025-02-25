'''
Created on 1/8/2016
'''

from django.conf.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from academic.api.views import ProcedureStepCommentAPI, ProcedureStepCommentTableView
from laboratory.api.shelfobject import ShelfObjectMaintanenceViewset, \
    ShelfObjectLogViewset, ShelfObjectCalibrateViewset, ShelfObjectGuaranteeViewset, \
    ShelfObjectTrainingViewset
from laboratory.shelfobject_container.views import show_shelf_container
from laboratory.shelfobject_container.viewsets import ContainerManagementViewset
from laboratory.views.catalogs import view_instrumental_family_list, \
    view_equipmenttype_list
from laboratory.views.shelfobject import view_equipment_shelfobject_detail
from sga.api.sga_components_viewsets import WarningWordAPI, WarningWordTableView, \
    DangerIndicationAPI, DangerIndicationTableView, \
    PrudenceAdviceAPI, PrudenceAdviceTableView
from authentication.users import ChangeUser, password_change, get_profile
from laboratory import views
from laboratory.api import shelfobject as ShelfObjectApi
from laboratory.api.views import ApiReservedProductsCRUD, ApiReservationCRUD, \
    CommentAPI, ProtocolViewSet, \
    LogEntryViewSet, InformViewSet, ShelfObjectAPI, ShelfObjectGraphicAPI, ShelfList, \
    ShelfObjectObservationView, EquipmentManagementViewset, \
    InstrumentalFamilyManagementViewset, EquipmentTypeManagementViewset, \
    ReactiveManagementViewset
from laboratory.functions import return_laboratory_of_shelf_id
from laboratory.protocol.views import protocol_list, ProtocolCreateView, ProtocolDeleteView, ProtocolUpdateView
from laboratory.reservation import ShelfObjectReservation
from laboratory.search import SearchDisposalObject
from laboratory.views import furniture, reports, shelfs, objectfeature
from laboratory.views import inform_period
from laboratory.views import labroom, shelfobject, laboratory, organizations
from laboratory.views.informs import get_informs, create_informs, complete_inform, remove_inform
from laboratory.views.laboratory import LaboratoryListView, LaboratoryDeleteView
from laboratory.views.logentry import get_logentry_from_organization
from laboratory.views.my_reservations import MyReservationView
from laboratory.views.objects import ObjectView, block_notifications, \
    view_equipment_list, view_reactive_list
from laboratory.views.organizations import OrganizationDeleteView, \
    OrganizationCreateView, OrganizationUpdateView, OrganizationActionsFormview
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
    path('rp/api/reservedProducts/<int:pk>/delete/', ApiReservedProductsCRUD.as_view(), name='api_reservation_delete'),
    path('rp/api/reservedProducts/<int:pk>/update/', ApiReservedProductsCRUD.as_view(), name='api_reservation_update'),
    path('r/api/reservation/', ApiReservationCRUD.as_view(), name='api_individual_reservation_create'),
    path('reserve_object/<int:modelpk>', ShelfObjectReservation.as_view(), name="object_reservation"),
    path('returnLabId', return_laboratory_of_shelf_id, name="get_lab_id"),
]

lab_shelf_urls = [
    #path('list/<int:furniture_pk>', shelfs.list_shelf, name="list_shelf"),
    path('create/', shelfs.ShelfCreate.as_view(), name="shelf_create"),
    path('delete/<int:pk>/<int:row>/<int:col>/', shelfs.delete_shelf, name="shelf_delete"),
    path('edit/<int:pk>/<int:row>/<int:col>/', shelfs.ShelfEdit.as_view(), name="shelf_edit"),
    path('containers/', show_shelf_container, name="shelf_containers"),

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
    path('get_shelfobject_limit/<int:pk>/', shelfobject.edit_limit_object, name="get_shelfobject_limit"),
    path('download_shelfobject_qr/<int:pk>/', shelfobject.download_shelfobject_qr, name="download_shelfobject_qr"),
    path('<int:pk>/log', ShelfObjectObservationView, name='get_shelfobject_log'),
]

lab_reports_urls = [
    # PDF reports
    path('shelf_objects/<int:pk>', reports.report_shelf_objects, name='reports_shelf_objects'),
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
    path('list/waste/report', reports.DiscardShelfReportView.as_view(), name='waste_report'),

]

lab_features_urls = [
    path('create/', objectfeature.FeatureCreateView.as_view(),
         name='object_feature_create'),
    path('edit/<int:pk>/', objectfeature.FeatureUpdateView.as_view(),
         name='object_feature_update'),
    path('delete/<int:pk>/', objectfeature.FeatureDeleteView.as_view(),
         name='object_feature_delete'),
]


reports_all_lab = [
    path('reports/hcode', laboratory.HCodeReports.as_view(), name='h_code_reports'),
    path('reports/download/hcode', reports.report_h_code, name='download_h_code_reports'),
    path('organizationreactivepresence/', reports.OrganizationReactivePresenceList.as_view(),
         name='organizationreactivepresence'),
]

sustance_urls = [
    path('', view_reactive_list, name='sustance_list'),
]

equipment_urls = [
    path('', view_equipment_list, name='equipment_list'),
    path('instrumental/', view_instrumental_family_list, name='instrumentalfamily_list'),
    path('equipmenttype/', view_equipmenttype_list, name='equipmenttype_list'),
]

organization_urls = [
    path('organization/manage/actions', OrganizationActionsFormview.as_view(),
         name='organization_actions'),
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
    path('shelf/shelfobject_status', furniture.add_catalog, kwargs={'key': 'shelfobject_status'}, name='add_shelfobject_status')
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
    path('create_user_qr/<int:pk>', laboratory.create_user_qr, name='create_user_qr'),
    path('create_user_qr/<int:pk>/<int:user>', laboratory.create_user_qr, name='create_user_qr'),
    path('redirect_user_to_labindex/<int:pk>/', laboratory.redirect_user_to_labindex, name='redirect_user_to_labindex'),
]

"""APIS"""
router = DefaultRouter()
comment_router = DefaultRouter()

comment_router.register('api_inform', CommentAPI, basename='api-inform')
router.register('api_protocol', ProtocolViewSet, basename='api-protocol')
router.register('api_logentry', LogEntryViewSet, basename='api-logentry')
router.register('api_informs', InformViewSet, basename='api-informs')

stepcommentsrouter = DefaultRouter()
stepcommentsrouter.register('api_my_procedure', ProcedureStepCommentAPI, basename='api-my-procedure')
stepcommentsrouter.register('api_procedure_comments', ProcedureStepCommentTableView, basename='api-procedure-comments')

sgacomponentsrouter = DefaultRouter()
sgacomponentsrouter.register('api_warning_word', WarningWordAPI, basename='api-warning-word')
sgacomponentsrouter.register('api_warnings_table', WarningWordTableView, basename='api-warnings-table')
sgacomponentsrouter.register('api_danger_indication', DangerIndicationAPI, basename='api-danger-indication')
sgacomponentsrouter.register('api_dangers_table', DangerIndicationTableView, basename='api-dangers-table')
sgacomponentsrouter.register('api_prudence_advice', PrudenceAdviceAPI, basename='api-prudence-advice')
sgacomponentsrouter.register('api_advices_table', PrudenceAdviceTableView, basename='api-advices-table')

shelfobjectrouter = DefaultRouter()
shelfobjectrouter.register('api_shelfobject_table', ShelfObjectApi.ShelfObjectTableViewSet, basename='api-shelfobjecttable')
shelfobjectrouter.register('api_shelfobject', ShelfObjectApi.ShelfObjectViewSet, basename='api-shelfobject')
shelfobjectrouter.register('api_search_labview', ShelfObjectApi.SearchLabView, basename='api-search-labview')

shelfcontainerrouter = DefaultRouter()
shelfcontainerrouter.register('api_container_list', ContainerManagementViewset, basename='api-container-in-shelf')

shelfobjectmaintenance = DefaultRouter()
shelfobjectmaintenance.register('api_shelfobject_maintenance_list', ShelfObjectMaintanenceViewset, basename='api-shelfobject-maintenance')

shelfobjectlog = DefaultRouter()
shelfobjectlog.register('api_shelfobject_log_list', ShelfObjectLogViewset, basename='api-shelfobject-log')

shelfobjectcalibrate_router = DefaultRouter()
shelfobjectcalibrate_router.register('api_shelfobject_calibrate', ShelfObjectCalibrateViewset, basename='api-shelfobject-calibrate')

shelfobjectguarantee_router = DefaultRouter()
shelfobjectguarantee_router.register('api_shelfobject_guarentee', ShelfObjectGuaranteeViewset, basename='api-shelfobject-guarantee')

shelfobjecttraining_router = DefaultRouter()
shelfobjecttraining_router.register('api_shelfobject_training', ShelfObjectTrainingViewset, basename='api-shelfobject-training')

equipment_shelfobject_url = [
    path('', view_equipment_shelfobject_detail, name='equipment_shelfobject_detail'),
]
objectrouter = DefaultRouter()
objectrouter.register('api_equipment_list', EquipmentManagementViewset, basename='api-equipment')
objectrouter.register('api_instrumentalfamily_list', InstrumentalFamilyManagementViewset, basename='api-instrumentalfamily')
objectrouter.register('api_equipmenttype_list', EquipmentTypeManagementViewset, basename='api-equipmenttype')
objectrouter.register("api_reactive_list", ReactiveManagementViewset, basename="api-reactive")




'''MULTILAB'''
urlpatterns += organization_urls + [
    path('<int:org_pk>/', include(organization_urls_org_pk)),
    path('inform_manager/<int:org_pk>/', include(informs_period_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/protocols/', include(lab_protocols_urls)),
    path('lab/<int:org_pk>/<int:pk>/delete/', LaboratoryDeleteView.as_view(), name="laboratory_delete"),
    path('lab/<int:org_pk>/search/disposal/', SearchDisposalObject.as_view(), name="disposal_substance"),
    path('lab/<int:org_pk>/<int:lab_pk>/rooms/', include(lab_rooms_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/furniture/', include(lab_furniture_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/objects/', include(objviews.get_urls())),
    path('lab/<int:org_pk>/<int:lab_pk>/reports/', include(lab_reports_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/shelfobject/', include(shelf_object_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/shelf/', include(lab_shelf_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/features/', include(lab_features_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/provider/', include(provider_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/informs/', include(informs_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/sustance/', include(sustance_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/equipment/', include(equipment_urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/blocknotifications/', block_notifications, name="block_notification"),
    path('so/api/<int:org_pk>/<int:lab_pk>/', include(shelfobjectrouter.urls)),
    path('so/api/<int:org_pk>/<int:lab_pk>/<int:shelf>/', include(shelfcontainerrouter.urls)),
    path('org/<int:org_pk>/api/shelfobject/',  ShelfObjectAPI.as_view(), name='api_shelfobject'),
    path('org/api/shelfobject/graphic',  ShelfObjectGraphicAPI.as_view(), name='api_shelfobject_graphic'),
    path('org/api/shels/list',  ShelfList.as_view(), name='get_shelfs_list'),
    path('<int:org_pk>/', include(reports_all_lab)),
    path('catalogs/', include(catalogs_urls)),
    path('inform/api/<int:org_pk>', include(comment_router.urls)),
    path('inform/api/', include(router.urls)),
    path('register_user_qr/<int:org_pk>/<int:lab_pk>/', include(user_register_qr)),
    path('spc/api/<int:org_pk>/<int:lab_pk>/', include(stepcommentsrouter.urls)),
    path('sga_components/api/<int:org_pk>/', include(sgacomponentsrouter.urls)),
    path('shelfobject/maintenance/api/<int:org_pk>/<int:lab_pk>/<int:shelfobject>/', include(shelfobjectmaintenance.urls)),
    path('shelfobject/log/api/<int:org_pk>/<int:lab_pk>/<int:shelfobject>/', include(shelfobjectlog.urls)),
    path('shelfobject/calibrate/api/<int:org_pk>/<int:lab_pk>/<int:shelfobject>/', include(shelfobjectcalibrate_router.urls)),
    path('shelfobject/guarantee/api/<int:org_pk>/<int:lab_pk>/<int:shelfobject>/', include(shelfobjectguarantee_router.urls)),
    path('shelfobject/training/api/<int:org_pk>/<int:lab_pk>/<int:shelfobject>/', include(shelfobjecttraining_router.urls)),
    path('lab/<int:org_pk>/<int:lab_pk>/shelfobject/<int:pk>/edit/', include(equipment_shelfobject_url)),
    path('equipment/api/<int:org_pk>/<int:lab_pk>/', include(objectrouter.urls)),
]
