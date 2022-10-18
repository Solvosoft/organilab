from django.urls import path

from auth_and_perms.views import organizationstructure as orgstruct

app_name='auth_and_perms'

urlpatterns = [
    path('organization/manage/',  orgstruct.organization_manage_view, name='organizationManager')
]