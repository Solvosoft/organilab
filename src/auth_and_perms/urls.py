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
    path('organization/manage/<int:org>/save',  orgstruct.save_rol_permission_organization, name='save_rol_permission_organization'),
    path('organization/manage/addusersorganization/<int:pk>/',  orgstruct.add_users_organization, name='addusersorganization'),
    path('organization/manage/users/add/', orgstruct.AddUser.as_view(), name="add_user"),
    path('organization/manage/rols/add/', orgstruct.add_rol_by_laboratory, name="add_rol_by_laboratory"),
]