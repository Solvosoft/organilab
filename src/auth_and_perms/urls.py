from django.urls import path, include, re_path

from auth_and_perms.api.viewsets import RolAPI, UpdateRolOrganizationProfilePermission, \
    OrganizationAPI, \
    UserLaboratoryOrganization, UserInOrganization, DeleteUserFromContenttypeViewSet, \
    ProfileToContenttypeObjectAPI, UpdateGroupsByProfile, SearchShelfObjectOrganization, \
    OrganizationButtons, ExternalUserToOrganizationViewSet
from auth_and_perms.views import organizationstructure as orgstruct

from rest_framework.routers import SimpleRouter

from auth_and_perms.views import user_org_creation
from auth_and_perms.views import fva_rest_authentication
from auth_and_perms.views.impostor import add_user_impostor, remove_impostor
from auth_and_perms.views.select_organization import select_organization_by_user
from authentication.views import SignDataRequestViewSet

routes = SimpleRouter()

routes.register('rol', RolAPI, 'api-rol' )
routes.register('profilepermissionrol', UpdateRolOrganizationProfilePermission, 'api-rolbyorg' )
routes.register('profilelaborgrol', UserLaboratoryOrganization, 'api-prolaborg' )
routes.register('profileinorgrol', UserInOrganization, 'api-userinorg' )
routes.register('extuserinorgrol', ExternalUserToOrganizationViewSet, 'api-extuserinorg' )
routes.register('deluserorgcontt', DeleteUserFromContenttypeViewSet, 'api-deluserorgcontt' )
routes.register('relusertocontenttype', ProfileToContenttypeObjectAPI, 'api-relusertocontenttype' )
routes.register('searchshelfobjectorg', SearchShelfObjectOrganization, 'api-searchshelfobjectorg' )

app_name='auth_and_perms'

urlpatterns = [
    path('organizations/', select_organization_by_user, name='select_organization_by_user'),
    path('api/', include(routes.urls)),
    path('switch_user/<int:org_pk>/<int:pk>', add_user_impostor, name="change_to_impostor"),
    path('end_switch_user', remove_impostor, name="remove_impostor"),
    path('login_bccr', fva_rest_authentication.login_with_bccr, name="login_with_bccr"),
    path('create_profile_by_digital_signature/<int:pk>', user_org_creation.create_profile_by_digital_signature, name="create_profile_by_digital_signature"),
    path('organization/registration',  user_org_creation.register_user_to_platform, name='register_user_to_platform'),
    path('registration/totp/<int:pk>/',  user_org_creation.create_profile_otp, name='user_org_creation_totp'),
    path('registration/digitalsignature/checkstatus',  fva_rest_authentication.check_signature_window_status_register, name='check_signature_window_status_register'),
    path('totp/img/<int:pk>/',  user_org_creation.show_QR_img, name='show_qr_img'),
    path('organization/manage/',  orgstruct.organization_manage_view, name='organizationManager'),
    path('organization/manage/addusersorganization/<int:pk>/',  orgstruct.add_users_organization, name='addusersorganization'),
    path('organization/manage/users/add/<int:pk>/', orgstruct.AddUser.as_view(), name="add_user"),
    path('organization/manage/rols/add/', orgstruct.add_rol_by_laboratory, name="add_rol_by_laboratory"),
    path('organization/manage/rols/list/<int:org_pk>/', orgstruct.ListRolByOrganization.as_view(), name="list_rol_by_org"),
    path('organization/manage/rols/del/<int:org_pk>/<int:pk>', orgstruct.DeleteRolByOrganization.as_view(), name="del_rol_by_org"),
    path('organization/manage/rols/copy/<int:pk>/', orgstruct.copy_rols, name="copy_rols"),
    path('organization/manage/relorgcont/add/', orgstruct.add_contenttype_to_org, name="add_contenttype_to_org"),
    path('digitalsignature/notify', SignDataRequestViewSet.as_view({'post': 'create'})),
    path('update_groups_by_profile/', UpdateGroupsByProfile.as_view(), name="api_update_groups_by_profile"),
    path('organization_buttons/', OrganizationButtons.as_view(), name="api_organization_buttons")
]
