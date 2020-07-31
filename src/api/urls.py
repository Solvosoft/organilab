from django.urls import path
from .access_management import OrganizationStructureView

urlpatterns = [
    path('access_management/', OrganizationStructureView.as_view(), name="api_organization_structure")
]