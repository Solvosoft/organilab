from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from auth_and_perms.models import ProfilePermission, Profile
from laboratory.models import OrganizationStructureRelations, OrganizationStructure


def user_is_allowed_on_organization(user, organization):
    if organization is None:
        raise ObjectDoesNotExist("Organization not found")
    if isinstance(organization, (str, int)):
        organization = get_object_or_404(OrganizationStructure, pk=organization)
    if not organization.users.filter(pk=user.pk).exists():
        raise PermissionDenied(
            _("User %(user)s not allowed on organization %(organization)r ")
            % {"user": user, "organization": organization}
        )


def user_is_allowed_on_laboratory(user, laboratory):
    if laboratory is None:
        raise ObjectDoesNotExist("Laboratory not found")
    profile = get_object_or_404(Profile, user=user)
    laboratories = profile.laboratories.all()
    for lab in laboratories:
        if lab.pk == laboratory.pk:
            return True
    raise PermissionDenied(
        _("User %(user)s not allowed on laboratory %(laboratory)r ")
        % {"user": user, "laboratory": laboratory}
    )


def organization_can_change_laboratory(laboratory, organization, raise_exec=False):
    if laboratory.organization == organization:
        return True
    if (
        OrganizationStructureRelations.objects.using(settings.READONLY_DATABASE)
            .filter(
            content_type__app_label=laboratory._meta.app_label,
            content_type__model=laboratory._meta.model_name,
            object_id=laboratory.pk,
            organization=organization,
        )
            .exists()
    ):
        return True

    if raise_exec:
        raise PermissionDenied(_("You can modify this laboratory"))
    return False
