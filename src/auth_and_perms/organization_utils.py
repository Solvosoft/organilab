from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from laboratory.models import OrganizationStructureRelations, OrganizationStructure
from laboratory.utils import get_users_from_organization


def user_is_allowed_on_organization(user, organization):
    if organization is None:
        raise ObjectDoesNotExist('Organization not found')


    users = list(get_users_from_organization(organization.pk, org=organization, userfilters={'users__isnull': False}))
    users= User.objects.filter(pk__in=set(users))

    if not users.filter(pk=user.pk).exists():
        raise PermissionDenied(_("User %(user)s not allowed on organization %(organization)r ")%{
            'user': user, 'organization': organization})


def organization_can_change_laboratory(laboratory, organization, raise_exec=False):
    if laboratory.organization == organization:
        return True
    if OrganizationStructureRelations.objects.filter(
        content_type__app_label=laboratory._meta.app_label,
        content_type__model=laboratory._meta.model_name,
        object_id=laboratory.pk,
        organization=organization
    ).exists():
        return True

    if raise_exec:
        raise PermissionDenied(_("You can modify this laboratory"))
    return False