from django.urls import path, include

from auth_and_perms.api.viewsets import RolAPI
from auth_and_perms.views import organizationstructure as orgstruct

from rest_framework.routers import SimpleRouter

routes = SimpleRouter()

routes.register('rol', RolAPI, 'api-rol' )
app_name='auth_and_perms'

urlpatterns = [
    path('api/', include(routes.urls)),
    path('organization/manage/',  orgstruct.organization_manage_view, name='organizationManager')
]