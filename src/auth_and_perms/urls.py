from django.urls import path, include

from auth_and_perms.api.viewsets import RolAPI, UpdateRolOrganizationProfilePermission, OrganizationAPI
from auth_and_perms.views import organizationstructure as orgstruct

from rest_framework.routers import SimpleRouter

from auth_and_perms.views import user_org_creation
from auth_and_perms.views import fva_rest_authentication

routes = SimpleRouter()

routes.register('rol', RolAPI, 'api-rol' )
routes.register('profilepermissionrol', UpdateRolOrganizationProfilePermission, 'api-rolbyorg' )

app_name='auth_and_perms'

urlpatterns = [
    path('api/', include(routes.urls)),
    path('login_bccr', fva_rest_authentication.login_with_bccr, name="login_with_bccr"),
    path('check_signature_window_status', fva_rest_authentication.check_signature_window_status, name="check_signature_window_status"),
    path('organization/registration',  user_org_creation.register_user_to_platform, name='register_user_to_platform'),
    path('registration/totp/<int:pk>/',  user_org_creation.create_profile_otp, name='user_org_creation_totp'),
    path('registration/digitalsignature/<int:pk>/',  user_org_creation.check_signature_window_status_register, name='check_signature_window_status_register'),
    path('totp/img/<int:pk>/',  user_org_creation.show_QR_img, name='show_qr_img'),
    path('organization/manage/',  orgstruct.organization_manage_view, name='organizationManager'),
    path('organization/manage/addusersorganization/<int:pk>/',  orgstruct.add_users_organization, name='addusersorganization'),
    path('organization/manage/users/add/<int:pk>/', orgstruct.AddUser.as_view(), name="add_user"),
    path('organization/manage/rols/add/', orgstruct.add_rol_by_laboratory, name="add_rol_by_laboratory"),
    path('organization/manage/rols/copy/<int:pk>/', orgstruct.copy_rols, name="copy_rols"),
    path('organization/manage/relorgcont/add/', orgstruct.add_contenttype_to_org, name="add_contenttype_to_org"),
]