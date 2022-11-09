from django.urls import path, include

from auth_and_perms.api.viewsets import RolAPI, UpdateRolOrganizationProfilePermission
from auth_and_perms.views import organizationstructure as orgstruct

from rest_framework.routers import SimpleRouter

routes = SimpleRouter()

routes.register('rol', RolAPI, 'api-rol' )
routes.register('profilepermissionrol', UpdateRolOrganizationProfilePermission, 'api-rolbyorg' )
app_name='auth_and_perms'

urlpatterns = [
    path('api/', include(routes.urls)),
    path('organization/manage/',  orgstruct.organization_manage_view, name='organizationManager'),
    path('organization/manage/addusersorganization/<int:pk>/',  orgstruct.add_users_organization, name='addusersorganization'),
    path('organization/manage/users/add/<int:pk>/', orgstruct.AddUser.as_view(), name="add_user"),
    path('organization/manage/rols/add/', orgstruct.add_rol_by_laboratory, name="add_rol_by_laboratory"),
    path('organization/manage/rols/copy/<int:pk>/', orgstruct.copy_rols, name="copy_rols"),
    path('organization/manage/relorgcont/add/', orgstruct.add_contenttype_to_org, name="add_contenttype_to_org"),
]