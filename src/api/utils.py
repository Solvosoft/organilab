import logging

from django.conf import settings
from djgentelella.permission_management import AllPermission, AllPermissionByAction
from rest_framework.generics import get_object_or_404

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import OrganizationStructure

logger = logging.getLogger("organilab")


class PermissionBase:
    def has_permission(self, request, view):
        organization = None
        if request.data and self.lookup_keyword in request.data:
            organization = request.data.get(self.lookup_keyword)
        if self.lookup_keyword in request.headers:
            organization = request.headers.get(self.lookup_keyword)
        if self.lookup_keyword in view.kwargs:
            organization = view.kwargs.get(self.lookup_keyword)
        if self.as_param_method is not None:
            organization = getattr(request, self.as_param_method.upper()).get(
                self.lookup_keyword
            )

        if organization is not None:
            try:
                organization = get_object_or_404(
                    OrganizationStructure.objects.using(settings.READONLY_DATABASE),
                    pk=organization,
                )
                user_is_allowed_on_organization(request.user, organization)
            except Exception as e:
                logger.warning("User not allowed to organization", exc_info=e)
                return False
        else:
            return False
        return super().has_permission(request, view)


class AllPermissionOrganization(AllPermission, PermissionBase):
    def __init__(self, perms, lookup_keyword="org_pk", as_param_method=None):
        self.lookup_keyword = lookup_keyword
        self.as_param_method = as_param_method

        super().__init__(perms)

    def __call__(self, *args, **kwargs):
        return self


class AllPermissionOrganizationByAction(AllPermissionByAction, PermissionBase):

    def __init__(self, lookup_keyword="org_pk"):
        self.lookup_keyword = lookup_keyword
        super().__init__()

    def __call__(self, *args, **kwargs):
        return self
