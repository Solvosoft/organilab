from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from auth_and_perms.models import ProfilePermission, Profile
from laboratory.models import OrganizationStructureRelations, OrganizationStructure, \
    UserOrganization


def user_is_allowed_on_organization(user, organization):

    if organization is None:
        raise ObjectDoesNotExist("Organization not found")

    if isinstance(organization, (str, int)):
        organization = get_object_or_404(OrganizationStructure, pk=organization)

    if organization.users.filter(pk=user.pk).exists():
        return True

    user_org_content_type = ContentType.objects.get_for_model(UserOrganization)
    user_org_ids = UserOrganization.objects.filter(user=user).values_list('pk',
                                                                          flat=True)
    has_relation = OrganizationStructureRelations.objects.filter(
        organization=organization,
        content_type=user_org_content_type,
        object_id__in=user_org_ids
    ).exists()

    if has_relation:
        return True

    for ancestor in organization.ancestors():
        if ancestor.users.filter(pk=user.pk).exists():
            return True
        has_ancestor_relation = OrganizationStructureRelations.objects.filter(
            organization=ancestor,
            content_type=user_org_content_type,
            object_id__in=user_org_ids
        ).exists()
        if has_ancestor_relation:
            return True

    raise PermissionDenied(
        _("User %(user)s not allowed on organization %(organization)r ")
        % {"user": user, "organization": organization}
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
